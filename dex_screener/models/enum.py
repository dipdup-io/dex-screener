from enum import StrEnum


class DexKey(StrEnum):
    IsolatedPool: str = 'hydradx_xyk'
    Omnipool: str = 'hydradx_omnipool'
    LBP: str = 'hydradx_lbp'
    StableSwap: str = 'hydradx_stableswap'
    OTC: str = 'hydradx_otc'
