from typing import Any

from dipdup import fields

from dex_screener.handlers.hydradx.asset.asset_count import DEX_SCREENER_PRICE_MAX_DIGITS
from dex_screener.handlers.hydradx.asset.asset_count import RUNTIME_BALANCE_MAX_DIGITS


class AccountField(fields.CharField):
    __module__ = 'dipdup.fields.AccountField'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(max_length=66, **kwargs)


class AssetAmountField(fields.CharField):
    __module__ = 'dipdup.fields.AssetAmountField'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(max_length=RUNTIME_BALANCE_MAX_DIGITS + 1, **kwargs)


class AssetPriceField(fields.CharField):
    __module__ = 'dipdup.fields.AssetAmountField'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(max_length=DEX_SCREENER_PRICE_MAX_DIGITS + 1, **kwargs)
