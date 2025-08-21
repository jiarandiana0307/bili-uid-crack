import os
import shlex
import subprocess
from tempfile import NamedTemporaryFile
from typing import List, Dict, Tuple, Optional

from packaging.version import Version

from .constants import *
from .utils import *
from .uid_range import UidRange


class BiliUidCrack:
    """实现破解功能的类。
    """

    def __init__(self, 
                 hashcat: Optional[str] = None,
                 john: Optional[str] = None,
                 backend_ignore_cuda: bool = False):
        self.__hashcat = None
        self.__hashcat_version = None
        try:
            self.__hashcat = get_hashcat_executable(hashcat)
            self.get_hashcat_version()
        except HashcatNotFoundException:
            pass

        self.__john = None
        self.__john_version = None
        try:
            self.__john = get_john_executable(john)
            self.get_hashcat_version()
        except JohnNotFoundException:
            pass

        if self.__hashcat is None and self.__john is None:
            raise NoAvailableCrackerException()

        self.__backend_ignore_cuda = backend_ignore_cuda

    def get_hashcat(self) -> str:
        """返回hashcat的绝对路径。

        Returns:
            str: hashcat的绝对路径。
        """
        return self.__hashcat

    def set_hashcat(self, hashcat: str):
        """自定义hashcat程序的路径。

        Args:
            hashcat (str): hashcatk程序的路径。
        """
        self.__hashcat = get_hashcat_executable(hashcat)
        self.update_hashcat_version()

    def get_john_the_ripper(self) -> str:
        """返回john程序的绝对路径。

        Returns:
            str: john程序的绝对路径。
        """
        return self.__john

    def set_john_the_ripper(self, john: str):
        self.__john = get_john_executable(john)

    def get_hashcat_version(self) -> Version:
        """返回当前实例中的hashcat版本。

        Returns:
            Version: hashcat的版本。
        """
        if self.__hashcat and self.__hashcat_version is None:
            self.__hashcat_version = Version(os.popen(f'"{self.__hashcat}" --version').read().strip())

        return self.__hashcat_version

    def get_john_version(self) -> Version:
        """返回当前实例中的john版本。

        Returns:
            Version: john的版本。
        """
        if self.__john and self.__john_version is None:
            version_str = os.popen(f'"{self.__john}"').read().strip().split('\n')[0].split()[3]
            self.__john_version = Version(version_str.split('-')[0])
        return self.__john_version

    @staticmethod
    def get_masks_and_charsets(is_standard_md5: bool, uid_range: UidRange) -> Dict[str, List[str]]:
        """获取用于生成候选UID的掩码和自定义字符集。

        Args:
            is_standard_md5 (bool): 是否为标准MD5。
            uid_range (UidRange): 指定破解的UID范围。

        Returns:
            Dict[str, List[str]]: 返回掩码和自定义字符集的映射，键为掩码，值为自定义字符串列表。
        """
        start_uid = str(uid_range.start)
        end_uid = str(uid_range.end)

        # 给起始UID从左补0直至和结尾UID等长，然后和结尾UID从左到右比较，两者首个不相同的字符称为边界字符，
        # 例如，起始UID和结尾UID分别为
        # 记录边界字符所在位置的索引值，这个值也是两者共同起始字符串的长度。
        boundary_index = 0
        prefixed_start = '0' * (len(end_uid) - len(start_uid)) + start_uid
        for i, (c1, c2) in enumerate(zip(prefixed_start, end_uid)):
            if c1 != c2:
                boundary_index = i
                break

        # 起始UID和结尾UID的共同起始字符串
        prefix = end_uid[:boundary_index]
        hex_prefix = ''.join([f'{int(x):02d}' for x in prefix])

        # 边界字符掩码的取值范围。
        boundary_mask_start = int(start_uid[boundary_index]) if len(start_uid) == len(end_uid) else 1
        boundary_mask_end = int(end_uid[boundary_index])

        # 边界字符的掩码的自定义字符集。
        boundary_charset = ''.join([str(x) for x in range(boundary_mask_start, boundary_mask_end + 1)])
        boundary_hex_charset = ''.join([f'{x:02d}' for x in range(boundary_mask_start, boundary_mask_end + 1)])

        # 边界字符右侧字符串的长度。
        suffix_len = len(end_uid) - len(prefix) - 1

        # 16进制自定义字符集
        hex_charset = ''.join([f'{x:02d}' for x in range(10)])

        masks_and_charsets = {}
        if is_standard_md5:
            if len(start_uid) == len(end_uid):
                if suffix_len > 0:
                    # 位于起始UID的边界字符的右边1位数。
                    digit_near_boundary_of_start_uid = start_uid[boundary_index+1]
                    if digit_near_boundary_of_start_uid != '0':
                        # 位于起始UID的边界字符右边1位数的字符集。
                        charset_near_boundary_of_start_uid = ''.join([str(x) for x in range(int(digit_near_boundary_of_start_uid), 10)])
                        mask = f"{prefix}{boundary_mask_start}?1{'?d' * (suffix_len - 1)}"
                        masks_and_charsets[mask] = [charset_near_boundary_of_start_uid]

                    # 位于结尾UID的边界字符的右边1位数
                    digit_near_boundary_of_end_uid = end_uid[boundary_index+1]

                    if (boundary_mask_end - boundary_mask_start > 1
                            or digit_near_boundary_of_start_uid != '0'
                            or digit_near_boundary_of_end_uid != '9'):
                        mask = f"{prefix}?1{'?d' * suffix_len}"
                        boundary_new_charset = boundary_charset
                        
                        if digit_near_boundary_of_start_uid != '0':
                            boundary_new_charset = boundary_new_charset[1:]

                        if digit_near_boundary_of_end_uid != '9':
                            boundary_new_charset = boundary_new_charset[:-1]

                        masks_and_charsets[mask] = [boundary_new_charset]

                    if digit_near_boundary_of_end_uid !='9':
                        # 位于结尾UID的边界字符右边1位数的字符集
                        charset_near_boundary_of_end_uid = ''.join([str(x) for x in range(0, int(digit_near_boundary_of_end_uid)+1)])
                        mask = f"{prefix}{boundary_mask_end}?1{'?d' * (suffix_len - 1)}"
                        masks_and_charsets[mask] = [charset_near_boundary_of_end_uid]

                else:
                    mask = f"{prefix}?1{'?d' * suffix_len}"
                    masks_and_charsets[mask] = [boundary_charset]

            else:
                charset_of_first_digit_of_start_uid = ''.join([str(x) for x in range(int(start_uid[0]), 10)])
                mask = f"?1{'?d' * (len(start_uid) - 1)}"
                masks_and_charsets[mask] = [charset_of_first_digit_of_start_uid]

                charset_of_first_digit_of_generated_uid = '123456789'
                if len(end_uid) - len(start_uid) > 1:
                    for mask_len in range(len(start_uid)+1, len(end_uid)):
                        mask = f"?1{'?d' * (mask_len - 1)}"
                        masks_and_charsets[mask] = [charset_of_first_digit_of_generated_uid]

                mask = f"?1{'?d' * (len(end_uid) - 1)}"
                masks_and_charsets[mask] = [boundary_charset]

        else:
            if len(start_uid) == len(end_uid):
                if suffix_len > 0:
                    # 位于起始UID的边界字符的右边1位数。
                    digit_near_boundary_of_start_uid = start_uid[boundary_index+1]
                    if digit_near_boundary_of_start_uid != '0':
                        # 位于起始UID的边界字符右边1位数的字符集。
                        hex_charset_near_boundary_of_start_uid = ''.join([f'{x:02d}' for x in range(int(digit_near_boundary_of_start_uid), 10)])
                        mask = f"{hex_prefix}{boundary_mask_start:02d}?2{'?1' * (suffix_len - 1)}"
                        masks_and_charsets[mask] = [hex_charset,hex_charset_near_boundary_of_start_uid]

                    # 位于结尾UID的边界字符的右边1位数
                    digit_near_boundary_of_end_uid = end_uid[boundary_index+1]

                    if (boundary_mask_end - boundary_mask_start > 1
                            or digit_near_boundary_of_start_uid != '0'
                            or digit_near_boundary_of_end_uid != '9'):
                        mask = f"{hex_prefix}?2{'?1' * suffix_len}"
                        boundary_new_hex_charset = boundary_hex_charset

                        if digit_near_boundary_of_start_uid != '0':
                            boundary_new_hex_charset = boundary_new_hex_charset[2:]

                        if digit_near_boundary_of_end_uid != '9':
                            boundary_new_hex_charset = boundary_new_hex_charset[:-2]

                        masks_and_charsets[mask] = [hex_charset, boundary_new_hex_charset]

                    if digit_near_boundary_of_end_uid != '9':
                        # 位于结尾UID的边界字符右边1位数的字符集
                        hex_charset_near_boundary_of_end_uid = ''.join([f'{x:02d}' for x in range(0, int(digit_near_boundary_of_end_uid)+1)])
                        mask = f"{hex_prefix}{boundary_mask_end:02d}?2{'?1' * (suffix_len - 1)}"
                        masks_and_charsets[mask] = [hex_charset, hex_charset_near_boundary_of_end_uid]

                else:
                    mask = f"{hex_prefix}?2{'?1' * suffix_len}"
                    masks_and_charsets[mask] = [hex_charset, boundary_hex_charset]

            else:
                hex_charset_of_first_digit_of_first_uid = ''.join([f'{x:02d}' for x in range(int(start_uid[0]), 10)])
                mask = f"?2{'?1' * (len(start_uid) - 1)}"
                masks_and_charsets[mask] = [hex_charset, hex_charset_of_first_digit_of_first_uid]

                hex_charset_of_first_digit_of_generated_uid = ''.join([f'{x:02d}' for x in range(1, 10)])
                if len(end_uid) - len(start_uid) > 1:
                    for mask_len in range(len(start_uid)+1, len(end_uid)):
                        mask = f"?2{'?1' * (mask_len - 1)}"
                        masks_and_charsets[mask] = [hex_charset, hex_charset_of_first_digit_of_generated_uid]

                mask = f"?2{'?1' * (len(end_uid) - 1)}"
                masks_and_charsets[mask] = [hex_charset, boundary_hex_charset]
        
        return masks_and_charsets

    @staticmethod
    def __generate_temp_hashcat_mask_file(masks_and_charsets: Dict[str, List[str]]) -> str:
        """创建用于提供hashcat掩码的临时文件。

        Args:
            masks_and_charsets (Dict[str, List[str]]): 返回掩码和自定义字符集的映射，键为掩码，值为自定义字符串列表。

        Returns:
            str: 创建的临时文件路径。
        """
        with NamedTemporaryFile('w', encoding='utf-8', suffix='.txt', prefix='hashcat_masks_', delete=False) as fp:
            maskfile = fp.name

            masks_and_charsets_str = ''
            for mask, charsets in masks_and_charsets.items():
                if len(charsets) > 0:
                    masks_and_charsets_str += ','.join(charsets) + ','
                masks_and_charsets_str += mask + '\n'
            fp.write(masks_and_charsets_str)

        return maskfile

    @staticmethod
    def __read_uid_from_hashcat_outfile(outfile: str) -> int:
        """从hashcat的输出文件中获取破解的UID值，若无破解的UID则返回-1。

        Args:
            outfile (str): hashcat输出文件路径。

        Returns:
            int: hashcat输出文件中已破解的UID，若无则返回-1。
        """
        with open(outfile, 'r', encoding='utf-8') as fp:
            uid = fp.read().strip()
        if uid != '':
            prefix = '$HEX['
            suffix = ']'
            if uid.startswith(prefix) and uid.endswith(suffix):
                uid = uid[len(prefix):-len(suffix)]
                return int(''.join([str(uid[x]) for x in range(1, len(uid), 2)]))
            else:
                return int(uid)
        else:
            return -1

    @staticmethod
    def __generate_temp_john_hash_file(md5: str) -> str:
        """创建用于给john程序传入哈希值的临时文件。

        Args:
            md5 (str): 待破解的16进制MD5值。

        Returns:
            str: 创建的临时文件路径。
        """
        with NamedTemporaryFile('w', encoding='utf-8', suffix='.txt', prefix='john_hash_', delete=False) as fp:
            hash_file = fp.name
            fp.write(md5)

        return hash_file

    @staticmethod
    def __generate_temp_john_pot_file() -> str:
        """创建临时文件用于保存john程序的输出结果。

        Returns:
            str: 创建的临时文件路径。
        """
        with NamedTemporaryFile('w', encoding='utf-8', suffix='.txt', prefix='john_pot_', delete=False) as fp:
            pot_file = fp.name
            fp.write('')
            
        return pot_file

    @staticmethod
    def __read_uid_from_john_pot_file(pot_file: str) -> int:
        """从john的输出文件中获取破解的UID，若无UID则返回-1。

        Args:
            pot_file (str): john的输出文件。

        Returns:
            int: hashcat输出文件中已破解的UID，若无则返回-1。
        """
        with open(pot_file, 'r', encoding='utf-8') as fp:
            text = fp.read().strip()
        if text == '':
            return -1
        else:
            return int(text.split(':')[-1])

    def crack_from_md5(self, md5: str, is_standard_md5: bool, uid_ranges: List[UidRange] = UID_RANGES_ALL) -> int:
        """根据MD5破解UID。

        若hashcat不可用则尝试john进行破解，反之，若john不可用时则尝试hashcat，当两者
        均不可用时抛出异常NoAvailableCrackerException。

        因为john不支持破解非标准MD5，所以如果使用john并且is_standard_md5为False时，
        抛出异常JohnCrackNonStandardMd5Exception。

        Args:
            md5 (str): 16进制MD5值。
            is_standard_md5 (bool): 指定是否为标准的MD5值。
            uid_ranges (List[UidRange], optional): 指定破解的UID范围，默认为所有可能的UID。

        Returns:
            int: 已破解的UID，若未破解则返回-1。
        """
        def hashcat_crack() -> Tuple[bool, int]:
            """运行hashcat进行破解。

            Returns:
                Tuple[bool, int]: 程序运行状态和UID。第一个值程序正常运行且无报错则返回True，运行失败返回False。
            """
            if self.__hashcat is None:
                False, -1

            with NamedTemporaryFile('w', encoding='utf-8', suffix='.txt', prefix='hashcat_outfile_', delete=False) as outfile_fp:
                outfile = outfile_fp.name

            uid_threshold = 10_000_000_000
            splited_uid_ranges = []
            for uid_range in uid_ranges:
                if uid_range.start < uid_threshold and uid_range.end >= uid_threshold:
                    # 将包含UID阈值的范围拆分为小于和大等于该阈值的范围
                    splited_uid_ranges.append(UidRange(uid_range.start, uid_threshold-1))
                    splited_uid_ranges.append(UidRange(uid_threshold, uid_range.end))
                else:
                    splited_uid_ranges.append(uid_range)

            returncode = 0
            for uid_range in splited_uid_ranges:
                masks_and_charsets = BiliUidCrack.get_masks_and_charsets(is_standard_md5, uid_range)
                maskfile = BiliUidCrack.__generate_temp_hashcat_mask_file(masks_and_charsets)
                workload_profile = 4
                if platform.system() == 'Windows' and uid_range.end < uid_threshold:
                    workload_profile = 1

                hashcat_cmd = f"\"{self.__hashcat}\" -m 0 -a 3 {'' if is_standard_md5 else '--hex-charset'} --outfile-format 2 --outfile \"{outfile}\" {'--backend-ignore-cuda' if self.__backend_ignore_cuda else ''} --potfile-disable --logfile-disable -O -w {workload_profile} --hwmon-disable {md5} \"{maskfile}\""
                process = subprocess.run(shlex.split(hashcat_cmd), cwd=os.path.split(self.__hashcat)[0])
                returncode = process.returncode

                if os.path.exists(maskfile):
                    os.remove(maskfile)

                uid = BiliUidCrack.__read_uid_from_hashcat_outfile(outfile)
                if returncode not in [0, 1] or uid > 0:
                    break

            if os.path.exists(outfile):
                os.remove(outfile)

            return (True, uid) if returncode in [0, 1] else (False, -1)

        def john_crack() -> Tuple[bool, int]:
            """运行john进行破解。

            Returns:
                Tuple[bool, int]: 程序运行状态和UID。第一个值程序正常运行且无报错则返回True，运行失败返回False。
            """
            if self.__john is None:
                return False, -1

            if not is_standard_md5:
                raise JohnCrackNonStandardMd5Exception('john不支持破解非标准MD5')

            pot_file = BiliUidCrack.__generate_temp_john_pot_file()

            masks_and_charsets = {}
            for uid_range in uid_ranges:
                masks_and_charsets.update(BiliUidCrack.get_masks_and_charsets(is_standard_md5, uid_range))

            uid = -1
            for mask, charsets in masks_and_charsets.items():
                john_hash_file = BiliUidCrack.__generate_temp_john_hash_file(md5)
                charsets_str = ' '.join([f'-{i+1}=\"{charset}\"' for i, charset in enumerate(charsets)])
                john_cmd = f'"{self.__john}" --format=raw-md5 {charsets_str} --mask="{mask}" --pot="{pot_file}" "{john_hash_file}"'
                process = subprocess.run(shlex.split(john_cmd), cwd=os.path.split(self.__john)[0])

                if process.returncode != 0:
                    if os.path.exists(pot_file):
                        os.remove(pot_file)
                    return False, -1

                uid = BiliUidCrack.__read_uid_from_john_pot_file(pot_file)

                if uid > 0:
                    break

            if os.path.exists(pot_file):
                os.remove(pot_file)

            return True, uid

        if not check_md5(md5):
            return -1

        uid_ranges = merge_uid_ranges(uid_ranges)

        uid = -1
        status = False
        if self.__hashcat:
            status, uid = hashcat_crack()
        if self.__john and not status:
            status, uid = john_crack()

        if not status:
            raise NoAvailableCrackerException()

        return uid

    def crack_from_url(self, url: str, uid_ranges: List[UidRange] = UID_RANGES_ALL) -> int:
        """根据B站网页端视频链接或视频分享链接破解UID。

        Args:
            url (str): 在用户已登录B站网页端的情况下得到的视频链接或视频分享链接。
            uid_ranges (List[UidRange], optional): 指定UID范围，默认为所有可能的UID。

        Returns:
            int: 已破解的UID，若未破解则返回-1。
        """
        if not check_crackable_url(url):
            return -1

        md5 = get_vd_source_from_url(url)
        is_standard_md5 = check_is_url_shared_from_web(url)
        return self.crack_from_md5(md5, is_standard_md5, uid_ranges)
