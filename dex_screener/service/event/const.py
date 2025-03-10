from enum import StrEnum


class DexScreenerEventType(StrEnum):
    Swap: str = 'Swap'
    Join: str = 'Join'
    Exit: str = 'Exit'
