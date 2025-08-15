"""
使用hashcat和（或）John the Ripper破解B站网页端视频链接或视频分享链接得到视频分享者的UID。

在登录B站网页端的情况下，B站视频页面的浏览器地址栏中的链接会自动加上一个
`vd_source`参数，在网页端点击视频分享按钮时得到的视频分享链接同样会有这个
参数，这个参数是当前用户UID的16进制MD5值，可以通过遍历计算UID的MD5值进行
MD5碰撞，当计算得到某个UID的MD5值等于链接中的MD5值时，说明这个UID就是此
链接的分享者。但是，浏览器地址栏的链接和点击分享按钮得到的链接中的`vd_source`
参数的值是不一样的，原因是两者计算得到MD5的方法不同。

在网页端通过点击分享按钮得到的视频分享链接中的`vd_source`参数是UID的标准
MD5值，计算方法是先将UID转为字符串，再将字符串逐个字符转为字节数组，比如
UID：123得到的字节数组是[0x31, 0x32, 0x33]，计算这个字节数组的16进制MD5值，
就得到标准MD5值。

直接在网页端打开视频页面，浏览器地址栏链接中自动添加的`vd_source`参数是UID的
非标准MD5值，计算方法是先将UID十进制数中的每一位数字直接放进字节数组，而无须
进行字符的转换，例如UID：123，得到的字节数组是[0x01, 0x02, 0x03]，计算这个
字节数组的16进制MD5值就得到非标准MD5值。

通过点击视频分享按钮得到的视频分享链接和浏览器地址栏中的视频链接在查询参数上
有明显区别，前者有一个`share_source=copy_web`的参数，而后者没有，通过这一差异
可以对两种链接进行区分。

注意，只有通过在网页端登录状态下得到的视频链接才有`vd_source`这一参数，通过
APP分享的视频链接是没有的，因而通过APP分享的视频链接无法反推UID，如果用户
未登录或手动删除了视频链接的`vd_source`参数也无法反推UID。

本工具支持使用hashcat和（或）John the Ripper进行破解，所以需要确保已安装
hashcat和（或）John the Ripper，并且添加进PATH环境变量， 或者使用--hashcat
和--john命令行参数分别指定hashcat程序和john程序的位置。

注意，John the Ripper只能用于破解标准MD5，也就是说，只能用于破解通过点击
视频分享按钮得到的视频分享链接中的MD5，这是因为此工具不支持空字符作为掩码。

作者：jiarandiana0307
项目地址：https://github.com/jiarandiana0307/bili-uid-crack
"""

import time
import argparse
from typing import Optional

from bili_uid_crack import *


def get_uid_ranges_from_args(args: Optional[argparse.Namespace]) -> List[UidRange]:
    """从命令行参数中获取指定的UID范围，若命令行参数没有提供UID范围则使用默认的UID范围。
    """
    uid_ranges = []
    if args.range is None:
        uid_ranges.extend(UID_RANGES_ALL)
    else:
        for uid_range in args.range:
            uid_range = UidRange(*uid_range)

            if uid_range.start > uid_range.end:
                raise Exception(f'无效的UID范围: [{uid_range.start}, {uid_range.end}]')

            uid_ranges.append(UidRange(uid_range.start, uid_range.end))
    return uid_ranges


def get_readable_time(total_seconds: float) -> str:
    seconds = int(total_seconds) % 60 + (total_seconds) - int(total_seconds)
    minutes = int((total_seconds) / 60) % 60
    hours = int((total_seconds) / 3600)
    return f"耗时: {hours:02d}:{minutes:02d}:{seconds:06.3f}"

    
def save_result(outfile: str, md5: str, uid: int, is_standard_md5: bool, uid_ranges: List[UidRange]):
    text = ''
    if uid > 0:
        text = f"MD5: {md5}\nUID: {uid}\nIsStandardMD5: {is_standard_md5}\n"
    else:
        text = f"MD5: {md5}\nUID: NotFound\nIsStandardMD5: Unknown\n"

    newline = '\n'
    if uid < 1:
        text += f"TriedUidRanges:\n{newline.join([str([x.start, x.end]) for x in uid_ranges])}\n"

    with open(outfile, 'w', encoding='utf-8') as fp:
        fp.write(text)


def main():
    filename = os.path.split(__file__)[1]
    parser = argparse.ArgumentParser(filename, description='使用hashcat破解B站网页端视频链接或视频分享链接得到视频分享者的UID。')
    parser.add_argument('-u', '--url', help='指定视频URL或视频分享URL。')
    parser.add_argument('-m', '--md5', help='指定MD5，通过-s和-ns参数指定是否为标准的MD5，若同时提供或都不提供这两个参数，则默认尝试标准和非标准的MD5。')
    parser.add_argument('-s', '--standard', action='store_true', help='传入MD5时，指定MD5来自于视频分享URL或为标准MD5。')
    parser.add_argument('-ns', '--non-standard', action='store_true', help='传入MD5时，指定MD5不是来自于视频分享URL或为非标准的MD5。')
    parser.add_argument('-r', '--range', action='append', nargs=2, type=int, help='指定破解的UID范围，可以多次使用此参数提供多个范围。缺省时默认尝试所有可能的UID。')
    parser.add_argument('--uid', help='获取指定UID的标准MD5和非标准MD5值。指定此参数时忽略其它参数')
    parser.add_argument('--hashcat', help='使用指定的hashcat破解程序。')
    parser.add_argument('--backend-ignore-cuda', action='store_true', help='在运行hashcat时忽略CUDA。当使用CUDA导致hashcat运行失败，报错"Kernel ./OpenCL/shared.cl build failed."时可以使用此参数解决。')
    parser.add_argument('--john', help='使用指定的John the Ripper破解程序，注意，若john只能破解标准MD5，无法破解非标准的MD5，也就是说john只能破解在网页端点击视频分享按钮得到的视频分享链接。')
    parser.add_argument('-o', '--outfile', help='指定结果的保存路径。')
    args = parser.parse_args()

    if args.uid is not None:
        print(f'获取UID: {args.uid} 的MD5')
        print(f'标准MD5: {uid_to_md5(args.uid, True)}')
        print(f'非标准MD5: {uid_to_md5(args.uid, False)}')
        return

    url = args.url
    md5 = args.md5
    if url is None and md5 is None:
        parser.print_help()
        return
    
    if md5 is not None and not check_md5(md5):
        print('不是有效的MD5:', md5)
        return
    
    if url is not None and not check_crackable_url(url):
        print(f'不是可破解的URL:', url)
        return

    if url is not None and check_crackable_url(url):
        md5 = get_vd_source_from_url(url)

    uid_ranges = []
    try:
        uid_ranges = get_uid_ranges_from_args(args)
        uid_ranges = merge_uid_ranges(uid_ranges)
    except Exception as e:
        print(e)
        return

    hashcat = None
    try:
        hashcat = get_hashcat_executable(args.hashcat)
    except HashcatNotFoundException as e:
        if args.hashcat is None:
            print('未找到hashcat程序。')
        else:
            print('未找到指定的hashcat程序:', args.hashcat)

    john = None
    try:
        john = get_john_executable(args.john)
    except JohnNotFoundException as e:
        if args.john is None:
            print('未找到john程序。')
        else:
            print('未找到指定的john程序:', args.john)

    outfile = None
    if args.outfile is not None:
        outfile = os.path.abspath(args.outfile)
        if os.path.exists(args.outfile) and os.path.isdir(args.outfile):
            print('无效的输出文件，存在同名文件夹', os.path.abspath(args.outfile))
            return

    try:
        cracker = BiliUidCrack(hashcat, john, args.backend_ignore_cuda)
    except NoAvailableCrackerException:
        print('未找到可用的hashcat或John the Ripper破解程序，请将hashcat或john程序所在目录添加至PATH系统环境变量，或使用--hashcat或--john参数分别指定破解程序的位置。')
        return

    if hashcat:
        hashcat_version = cracker.get_hashcat_version().base_version
        print(f'已找到hashcat v{hashcat_version}:', hashcat)

    if john:
        john_version = cracker.get_john_version().base_version
        print(f'已找到john v{john_version}:', john)

    print(f'开始破解MD5: {md5}')

    print('尝试破解的UID范围：')
    for uid_range in uid_ranges:
        print(f'[{uid_range.start}, {uid_range.end}]')
    print()

    uid = -1
    start = time.time()

    is_standard_md5 = None

    try:
        if url is not None:
            uid = cracker.crack_from_url(url, uid_ranges)
            is_standard_md5 = check_is_url_shared_from_web(url)

        else:
            if args.standard and not args.non_standard:
                uid = cracker.crack_from_md5(md5, args.standard, uid_ranges)
                is_standard_md5 = True

            elif not args.standard and args.non_standard:
                uid = cracker.crack_from_md5(md5, args.standard, uid_ranges)
                is_standard_md5 = False

            else:
                if hashcat is None and john is not None:
                    raise JohnCrackNonStandardMd5Exception()

                for uid_range in uid_ranges:
                    count = uid_range.end - uid_range.start + 1
                    print(f'正在尝试{uid_range.start}到{uid_range.end}共{count}个UID\n')

                    uid = cracker.crack_from_md5(md5, True, [uid_range])
                    is_standard_md5 = True
                    if uid == -1:
                        uid = cracker.crack_from_md5(md5, False, [uid_range])
                        is_standard_md5 = False

                    if uid > 0:
                        break

    except JohnCrackNonStandardMd5Exception:
        if url is None:
            print('John the Ripper不支持破解非标准MD5。请使用hashcat破解非标准MD5。')
        else:
            print('John the Ripper不支持破解非标准MD5，传入的URL来自浏览器地址栏，其中的MD5是非标准的MD5，不支持使用john进行破解。请使用hashcat破解非标准MD5。')
        return

    except NoAvailableCrackerException:
        if hashcat:
            print('hashcat运行失败。')
        if john:
            print('John the Ripper运行失败。')
        print('破解程序运行失败，退出程序。')
        return

    print()
    
    end = time.time()
    print()

    if uid > 0:
        print('已破解MD5:', md5)
        print(f"MD5为{'标准' if is_standard_md5 else '非标准'}MD5，来自于网页端{'视频分享链接' if is_standard_md5 else '视频链接'}")
        print(f'UID为: {uid}')

    else:
        print('未能破解MD5:', md5)

    cost_time = get_readable_time(end - start)
    print(cost_time)

    if outfile is not None:
        save_result(outfile, md5, uid, is_standard_md5, uid_ranges)

        print('已保存结果至', f'"{outfile}"')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n退出程序。')
