from enum import StrEnum


class DexScreenerEventType(StrEnum):
    Swap = 'Swap'
    Join = 'Join'
    Exit = 'Exit'
