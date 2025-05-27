from enum import StrEnum


class DexKey(StrEnum):
    IsolatedPool = 'hydradx_xyk'
    Omnipool = 'hydradx_omnipool'
    LBP = 'hydradx_lbp'
    StableSwap = 'hydradx_stableswap'
    OTC = 'hydradx_otc'
