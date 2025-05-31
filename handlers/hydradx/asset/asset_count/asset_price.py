from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from typing import Generic
from typing import TypeVar
from typing import overload

from dex_screener.handlers.hydradx.asset.asset_count import DEX_SCREENER_PRICE_MAX_DECIMALS
from dex_screener.handlers.hydradx.asset.asset_count import DEX_SCREENER_PRICE_MAX_DIGITS
from dex_screener.handlers.hydradx.asset.asset_count.asset_amount import AssetAmount
from dex_screener.handlers.hydradx.asset.asset_count.types import AnyTypeDecimal

if TYPE_CHECKING:
    from typing import Self

    from dex_screener.handlers.hydradx.asset.asset_count.market_pair import MarketPair

from dex_screener.handlers.hydradx.asset.asset_count.market_pair import MarketPairBaseAsset
from dex_screener.handlers.hydradx.asset.asset_count.market_pair import MarketPairQuoteAsset
from dex_screener.handlers.hydradx.asset.asset_count.types import AnyTypePrice

MarketPairBaseAssetAmount = TypeVar('MarketPairBaseAssetAmount', bound=AssetAmount)
MarketPairQuoteAssetAmount = TypeVar('MarketPairQuoteAssetAmount', bound=AssetAmount)


class AssetPrice(Generic[MarketPairBaseAsset, MarketPairQuoteAsset]):
    def __init__(self, price: AnyTypePrice, market_pair: MarketPair[MarketPairBaseAsset, MarketPairQuoteAsset]):
        self.pair: MarketPair = market_pair
        if not isinstance(price, Decimal):
            price = Decimal(price)
        _, digits, exponent = price.as_tuple()
        decimals_limit = min(
            (DEX_SCREENER_PRICE_MAX_DIGITS - (len(digits) + exponent)),  # type: ignore[operator]
            DEX_SCREENER_PRICE_MAX_DECIMALS,
        )
        self.price: Decimal = price.quantize(Decimal(f'1e{-decimals_limit}'))

    @overload
    def __rtruediv__(self: Self, other: AnyTypeDecimal) -> AssetPrice[MarketPairQuoteAsset, MarketPairBaseAsset]: ...
    @overload
    def __rtruediv__(self: Self, other: MarketPairQuoteAssetAmount) -> MarketPairBaseAssetAmount: ...  # type: ignore[overload-cannot-match,type-var,misc]
    def __rtruediv__(self, other):
        if isinstance(other, AssetAmount):
            if other.asset.id != self.pair.quote.id:
                raise TypeError(f'Can only divide {self.pair!s} price with {self.pair.quote} amount')
            return self.pair.base.amount(Decimal(other) / self.price)

        if isinstance(other, AnyTypeDecimal):
            return AssetPrice(Decimal(other) / self.price, self.pair.reverse())
        raise TypeError('Unsupported operand type')

    def reverse(self) -> AssetPrice[MarketPairQuoteAsset, MarketPairBaseAsset]:
        return self.__rtruediv__(1)

    def __add__(self: Self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            raise TypeError(f'Cannot add {self.pair} to {type(other).__name__}')

        if other.pair != self.pair:
            raise TypeError(f'Cannot add {self.pair} to {other.pair}')
        result = self.price + other.price
        return AssetPrice(result, self.pair)  # type: ignore[return-value]

    def __sub__(self: Self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            raise TypeError(f'Cannot subtract {type(other).__name__} from {self.pair}')

        if other.pair != self.pair:
            raise TypeError(f'Cannot subtract {other.pair} from {self.pair}')
        result = self.price - other.price
        return AssetPrice(result, self.pair)  # type: ignore[return-value]

    @overload
    def __mul__(  # type: ignore[overload-overlap]
        self: AssetPrice[MarketPairBaseAsset, MarketPairQuoteAsset], other: MarketPairBaseAssetAmount
    ) -> MarketPairQuoteAssetAmount: ...  # type: ignore[type-var,misc]
    @overload
    def __mul__(
        self: AssetPrice[MarketPairBaseAsset, MarketPairQuoteAsset], other: AnyTypeDecimal
    ) -> AssetPrice[MarketPairBaseAsset, MarketPairQuoteAsset]: ...
    def __mul__(self, other):
        if isinstance(other, AssetAmount):
            if other.asset.id != self.pair.base.id:
                raise TypeError(f'Can only multiply {self.pair!s} price with {self.pair.base.__name__} amount')
            return self.pair.quote.amount(self.price * Decimal(other))
        if isinstance(other, AnyTypeDecimal):
            result = self.price * Decimal(other)
            return AssetPrice(result, self.pair)
        raise TypeError('Unsupported operand type')

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self: Self, other: AnyTypeDecimal) -> Self:
        if isinstance(other, AnyTypeDecimal):
            result = self.price / Decimal(other)
            return AssetPrice(result, self.pair)  # type: ignore[return-value]
        raise TypeError('Unsupported operand type')

    def __eq__(self, other: AssetPrice[MarketPairBaseAsset, MarketPairQuoteAsset]) -> bool:  # type: ignore[override]
        if not isinstance(other, AssetPrice):
            raise TypeError('Can only compare AssetPrice with AssetPrice')
        return self.pair == other.pair and self.price.normalize() == other.price.normalize()

    def __str__(self) -> str:
        return f'{self.price.normalize():f}'

    def __repr__(self) -> str:
        return f'{self.pair!s}({self})'
