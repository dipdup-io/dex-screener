from enum import StrEnum


class HydrationAssetType(StrEnum):
    Token: str = 'Token'
    External: str = 'External'
    StableSwap: str = 'StableSwap'
    Bond: str = 'Bond'
    PoolShare: str = 'PoolShare'
    XYK: str = 'XYK'
    ERC20: str = 'Erc20'
