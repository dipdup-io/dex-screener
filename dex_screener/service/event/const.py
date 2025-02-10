from enum import StrEnum


class DexScreenerEventType(StrEnum):
    swap: str = 'swap'
    join: str = 'join'
    exit: str = 'exit'
