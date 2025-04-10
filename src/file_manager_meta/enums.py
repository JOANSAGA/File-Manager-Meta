from enum import Enum


class SortBy(str, Enum):
    EXT = "ext"
    DATE = "date"
    SIZE = "size"
