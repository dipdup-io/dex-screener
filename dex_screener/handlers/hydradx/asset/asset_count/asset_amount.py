from __future__ import annotations

from typing import TYPE_CHECKING
from typing import overload

from .types import AnyTypeDecimal

if TYPE_CHECKING:
    from dex_screener.models import Asset

    from .asset_price import AssetPrice
    from .types import AnyTypeAmount

from decimal import Decimal
from typing import Self


def _prepare(amount: AnyTypeAmount, decimals: int) -> Decimal:
    if not isinstance(amount, Decimal):
        amount = Decimal(amount)

    if amount == amount.to_integral():
        amount = amount.quantize(Decimal(1))
    else:
        amount = amount.normalize()

    return amount.quantize(Decimal(f'1e-{decimals}'))


class AssetAmount(Decimal):
    def __new__(cls, asset: Asset, amount: AnyTypeAmount):
        amount = _prepare(amount, asset.decimals)
        new: Self = Decimal.__new__(AssetAmount, amount)
        new.__init__(asset, amount)
        return new

    def __init__(self, asset: Asset, amount: Decimal, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.asset = asset
        self.amount: Decimal = _prepare(amount, asset.decimals)

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
    def __rtruediv__(self: Self, other: AssetAmount) -> AssetPrice: ...
    @overload
    def __rtruediv__(self: Self, other: Self) -> Decimal: ...

    def __rtruediv__(self, other):
        if not isinstance(other, AssetAmount):
            raise TypeError(f'Cannot divide {type(other).__name__} by {self.asset}')
        if self.asset.id != other.asset.id:
            from .asset_price import AssetPrice
            from .market_pair import MarketPair

            pair = MarketPair(self.asset, other.asset)
            price = other.amount / self.amount
            return AssetPrice(price, pair)

        return Decimal(other) / Decimal(self.amount)

    @overload
    def __truediv__(self: Self, other: AssetAmount) -> AssetPrice: ...
    @overload
    def __truediv__(self: Self, other: AssetPrice) -> AssetAmount: ...
    @overload
    def __truediv__(self: Self, other: Self) -> Decimal: ...
    @overload
    def __truediv__(self: Self, other: AnyTypeDecimal) -> Self: ...

    def __truediv__(self: Self, other):
        from .asset_price import AssetPrice

        if isinstance(other, AssetAmount):
            return other.__rtruediv__(self)
        if isinstance(other, AssetPrice):
            return other.__rtruediv__(self)
        if isinstance(other, AnyTypeDecimal):
            return AssetAmount(asset=self.asset, amount=self.amount / Decimal(other))

        raise TypeError('Unsupported operand type')

    def __str__(self: Self) -> str:
        return f'{self.amount.normalize():f}'

    def __repr__(self: Self) -> str:
        return f'{self.asset.symbol}({self!s})'
