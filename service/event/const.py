from enum import StrEnum


class DexScreenerEventType(StrEnum):
    Swap = 'swap'
    Join = 'join'
    Exit = 'exit'
