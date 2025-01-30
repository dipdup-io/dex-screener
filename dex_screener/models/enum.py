from enum import StrEnum


class DexKey(StrEnum):
    hydradx: str = 'hydradx'
    IsolatedPool: str = 'hydradx_xyk'
    OmniPool: str = 'hydradx_omnipool'
    StableSwap: str = 'hydradx_stableswap'
