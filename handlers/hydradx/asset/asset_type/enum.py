from enum import StrEnum


class HydrationAssetType(StrEnum):
    Token = 'Token'
    External = 'External'
    StableSwap = 'StableSwap'
    Bond = 'Bond'
    PoolShare = 'PoolShare'
    XYK = 'XYK'
    ERC20 = 'Erc20'
