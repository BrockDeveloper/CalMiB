from enum import Enum

class FilterMode(str, Enum):
    whitelist = 'whitelist'
    blacklist = 'blacklist'
