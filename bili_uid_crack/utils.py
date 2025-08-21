import re
import os
import shutil
import hashlib
import platform
from typing import List, Optional
from urllib.parse import urlparse, parse_qs

import curl_cffi

from .exceptions import *
from .uid_range import UidRange


def check_md5(md5: Optional[str]) -> bool:
    """判断是否为有效的16进制MD5值。

    Args:
        md5 (Optional[str]): 16进制MD5值。

    Returns:
        bool: 当md5为16进制MD5字符串时返回True，否则返回False。
    """
    return re.match('^[a-f\\d]{32}$', md5.lower()) is not None


def check_crackable_url(url: Optional[str]) -> bool:
    """判断是否为可破解的链接。

    Args:
        url (Optional[str]): 在用户已登录B站网页端的情况下得到的视频链接或视频分享链接。

    Returns:
        bool: 当URL有vd_source参数且值为16进制MD5时返回True，否则返回False。
    """
    return len(get_vd_source_from_url(url)) > 0


def check_is_url_shared_from_web(url: str) -> bool:
    """判断URL是否为B站网页端的视频分享链接。

    当URL为B站网页端的视频分享链接（即通过在网页端点击视频分享按钮生成的链接）时，
    链接中的`vd_source`参数为标准的MD5，否则为非标准的MD5。

    Args:
        url (str): B站网页端的视频链接或视频分享链接。

    Returns:
        bool: URL是否为B站网页端的视频分享链接。
    """
    query = parse_qs(urlparse(url).query)
    share_source = query.get('share_source', [''])[0]
    return share_source == 'copy_web'


def get_hashcat_executable(hashcat: Optional[str] = None) -> str:
    """获取hashcat的可执行程序的绝对路径。

    Args:
        hashcat (Optional[str], optional): hashcat程序的路径。

    Returns:
        str: hashcat可执行程序的绝对路径，若未找到hashcat程序则返回空字符串。
    """
    hashcat_abspath = None
    if hashcat is None:
        hashcat_abspath = shutil.which('hashcat.exe' if platform.system() == 'Windows' else 'hashcat')
        if hashcat_abspath is None:
            hashcat_abspath = shutil.which('hashcat')
    else:
        path, name = os.path.split(hashcat)
        if path == '':
            path = None
        hashcat = shutil.which(name, path=path)
        if hashcat:
            hashcat_abspath = os.path.abspath(hashcat)

    if hashcat_abspath is None or not os.popen(f'{hashcat_abspath} --version').read().startswith('v'):
        raise HashcatNotFoundException('未找到hashcat程序' + str(hashcat))

    return hashcat_abspath

    
def get_john_executable(john: Optional[str] = None) -> str:
    """获取John the Ripper的可执行程序的绝对路径。

    Args:
        john (Optional[str], optional): john程序的路径。

    Returns:
        str: john可执行程序的绝对路径，若未找到john程序则返回空字符串。
    """
    john_abspath = None
    if john is None:
        john_abspath = shutil.which('john.exe' if platform.system() == 'Windows' else 'john')
    else:
        path, name = os.path.split(john)
        if path == '':
            path = None
        john = shutil.which(name, path=path)
        if john:
            john_abspath = os.path.abspath(john)

    if john_abspath is None or not os.popen(john_abspath).read().startswith('John the Ripper'):
        raise JohnNotFoundException('未找到john程序' + str(john))

    return john_abspath


def get_vd_source_from_url(url: str) -> str:
    """从URL的中获取vd_source参数，这是一个16进制的MD5值。

    Args:
        url (str): 在用户已登录B站网页端的情况下得到的视频链接或视频分享链接。

    Returns:
        str: 16进制MD5值，若失败则返回空字符串。
    """
    query = parse_qs(urlparse(url).query)
    vd_source = query.get('vd_source', [''])[0]
    return vd_source if check_md5(vd_source) else ''


def uid_to_md5(uid: int, is_standard_md5: bool) -> str:
    """将UID转为MD5。

    Args:
        uid (int): 用户ID。
        is_standard_md5 (bool): 指定是否通过标准的方法转换为16进制MD5值。

    Returns:
        str: 16进制MD5值。
    """
    if is_standard_md5:
        return hashlib.md5(str(uid).encode('ascii')).hexdigest()
    else:
        return hashlib.md5(bytes([int(x) for x in str(uid)])).hexdigest()

def merge_uid_ranges(uid_ranges: List[UidRange]) -> List[UidRange]:
    """合并重叠的UID范围。

    Args:
        uid_ranges (List[UidRange]): UID范围的列表。

    Returns:
        List[UidRange]: 合并后的UID范围的列表。
    """
    if len(uid_ranges) < 1:
        return []
    
    sorted_ranges = sorted(uid_ranges, key=lambda x: x.start)
    merged = [sorted_ranges[0]]
    
    for current_start, current_end in sorted_ranges[1:]:
        last_start, last_end = merged[-1]
        if current_start <= last_end:
            new_end = max(last_end, current_end)
            merged[-1] = UidRange(last_start, new_end)
        else:
            merged.append(UidRange(current_start, current_end))

    return merged


def query_uid_with_md5(md5: str, **kwargs) -> int:
    """使用aicu.cc查询MD5对应的UID。

    Args:
        md5 (str): 待查询的16进制MD5。
        **kwargs: curl_cffi.request()的参数。

    Raises:
        Exception: aicu.cc查询服务异常。

    Returns:
        int: 返回查询得到的UID，若无则返回-1。
    """
    uid = -1
    url = f'https://api.aicu.cc/api/v3/tool/hash2uid?hash={md5}'
    response = curl_cffi.get(url, impersonate='chrome110', **kwargs)
    response.raise_for_status()

    if response.text != '':
        uid = int(response.json()['data']['uid'])

    return uid


def query_uid_with_url(url: str, **kwargs) -> int:
    """使用aicu.cc查询URL中MD5对应的UID。

    Args:
        url (str): 网页端频链接或视频分享链接。
        **kwargs: curl_cffi.request()的参数。

    Returns:
        int: 返回查询得到的UID，若无则返回-1。
    """
    if not check_crackable_url(url):
        return -1

    md5 = get_vd_source_from_url(url)
    return query_uid_with_md5(md5, **kwargs)