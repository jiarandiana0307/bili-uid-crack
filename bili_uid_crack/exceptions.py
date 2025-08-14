class HashcatNotFoundException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class JohnNotFoundException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class JohnCrackNonStandardMd5Exception(Exception):
    """John the Ripper程序不支持破解非标准的MD5。
    """
    def __init__(self, *args):
        super().__init__(*args)


class NoAvailableCrackerException(Exception):
    """没有可用的破解程序。
    """
    def __init__(self, *args):
        super().__init__(*args)