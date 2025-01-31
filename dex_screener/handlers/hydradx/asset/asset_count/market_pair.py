from __future__ import annotations

from typing import Generic
from typing import TypeVar

MarketPairBaseAsset = TypeVar('MarketPairBaseAsset', bound='Asset')
MarketPairQuoteAsset = TypeVar('MarketPairQuoteAsset', bound='Asset')


class MarketPair(Generic[MarketPairBaseAsset, MarketPairQuoteAsset]):
    def __init__(self, pair_base_asset: MarketPairBaseAsset, pair_quote_asset: MarketPairQuoteAsset):
        if pair_base_asset is pair_quote_asset:
            raise ValueError('Different Assets expected')

        self.base: MarketPairBaseAsset = pair_base_asset
        self.quote: MarketPairQuoteAsset = pair_quote_asset

    @property
    def decimals(self) -> int:
        return self.base.decimals + self.quote.decimals

    def reverse(self) -> MarketPair[MarketPairQuoteAsset, MarketPairBaseAsset]:
        return MarketPair(self.quote, self.base)

    def __eq__(self, other: MarketPair) -> bool:
        if not isinstance(other, MarketPair):
            raise TypeError('Can only compare MarketPair with MarketPair')
        return self.base.id == other.base.id and self.quote.id == other.quote.id

    def __repr__(self) -> str:
        return f'<{type(self).__name__}: base={self.base}, quote={self.quote}>'

    def __str__(self) -> str:
        return '/'.join([str(self.base), str(self.quote)])
