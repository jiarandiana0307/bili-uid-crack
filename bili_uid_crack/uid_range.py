class UidRange:
    def __init__(self, start: int, end: int):
        if start > end:
            raise ValueError('起始UID不能大于结尾UID')

        self.start = start
        self.end = end