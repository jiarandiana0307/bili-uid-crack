class UidRange:
    def __init__(self, start, end):
        if start > end:
            raise ValueError('起始UID必须小于等于结尾UID')
        self._start = start
        self._end = end
    
    @property
    def start(self):
        return self._start
    
    @property
    def end(self):
        return self._end
    
    def __getitem__(self, index):
        if index == 0:
            return self._start
        elif index == 1:
            return self._end
        else:
            raise IndexError('UidRange索引超出范围')
    
    def __len__(self):
        return 2
    
    def __eq__(self, other):
        if not isinstance(other, UidRange):
            return False
        return self._start == other._start and self._end == other._end
    
    def __hash__(self):
        return hash((self._start, self._end))
    
    def __repr__(self):
        return f'UidRange({self._start}, {self._end})'
    
    def __iter__(self):
        yield self._start
        yield self._end
    
    def __contains__(self, item):
        """检查给定的UID是否在此范围内"""
        return self._start <= item <= self._end
    
    def overlaps(self, other):
        """检查此范围是否与另一个范围重叠"""
        if not isinstance(other, UidRange):
            raise TypeError('不是UidRange类型')
        return self._start <= other._end and self._end >= other._start
    
    def merge(self, other):
        """合并两个重叠的范围"""
        if not self.overlaps(other):
            raise ValueError('无法合并两个不重叠的UID范围')
        return UidRange(min(self._start, other._start), max(self._end, other._end))