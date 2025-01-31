from __future__ import annotations

from typing import TYPE_CHECKING
from typing import overload

if TYPE_CHECKING:
    from dex_screener.models import Asset

    from .asset_price import AssetPrice
    from .market_pair import MarketPairBaseAsset
    from .market_pair import MarketPairQuoteAsset
    from .types import AnyTypeAmount

from decimal import Decimal
from typing import Self


class AssetAmount(Decimal):
    def __new__(cls, asset: Asset, amount: AnyTypeAmount):
        amount = Decimal(amount).quantize(Decimal('1.' + '0' * asset.decimals))
        return super().__new__(cls, amount)

    def __init__(self, asset: Asset, amount: AnyTypeAmount):
        self.asset = asset
        self.amount = amount

    @property
    def minor(self: Self) -> int:
        return self.asset.to_minor(self)

    def __add__(self: Self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            raise TypeError(f'Cannot add {self.asset} to {type(other).__name__}')
        if self.asset.id != other.asset.id:
            raise TypeError(f'Cannot add {self.asset} to {other.asset}')
        result = Decimal.__add__(self, other)
        return AssetAmount(asset=self.asset, amount=result)

    def __sub__(self: Self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            raise TypeError(f'Cannot subtract {type(other).__name__} from {self.asset}')
        if self.asset.id != other.asset.id:
            raise TypeError(f'Cannot subtract {other.asset} from {self.asset}')
        result = Decimal.__sub__(self, other)
        return AssetAmount(asset=self.asset, amount=result)

    @overload
    def __rtruediv__(self: Self, other: Self) -> Decimal: ...
    @overload
    def __rtruediv__(self: Self, other: AssetAmount) -> AssetPrice: ...

    def __rtruediv__(self, other):
        if not isinstance(other, AssetAmount):
            raise TypeError(f'Cannot divide {type(other).__name__} by {self.asset}')
        if self.asset.id != other.asset.id:
            from .asset_price import AssetPrice
            from .market_pair import MarketPair

            pair = MarketPair(self.asset, other.asset)
            return AssetPrice(Decimal(other.amount) / Decimal(self.amount), pair)

        return (Decimal(other) / Decimal(self.amount)).quantize(Decimal('1.' + '0' * self.asset.decimals))

    def __truediv__(self: Self, other: AssetPrice[MarketPairQuoteAsset, MarketPairBaseAsset]) -> MarketPairBaseAsset:
        from .asset_price import AssetPrice

        if isinstance(other, AssetPrice):
            return other.__rtruediv__(self)
        if isinstance(other, AssetAmount):
            return other.__rtruediv__(self)
        raise TypeError('Unsupported operand type')

    def __repr__(self: Self) -> str:
        return f'{self.asset.symbol}({self!s})'
