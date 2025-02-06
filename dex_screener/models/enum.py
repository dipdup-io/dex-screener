from enum import StrEnum


class DexKey(StrEnum):
    IsolatedPool: str = 'hydradx_xyk'
    Omnipool: str = 'hydradx_omnipool'
    StableSwap: str = 'hydradx_stableswap'
