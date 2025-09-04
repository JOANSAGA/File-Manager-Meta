from enum import Enum


class SortBy(str, Enum):
    EXT = "ext"
    DATE = "date"
    SIZE = "size"


class KeepRule(str, Enum):
    oldest = "oldest"


class DateGranularity(str, Enum):
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
