from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING
from typing import Any
from typing import no_type_check

from dipdup import fields
from scalecodec import is_valid_ss58_address  # type: ignore[import-untyped]
from scalecodec import ss58_decode

from dex_screener.handlers.hydradx.asset.asset_count import DEX_SCREENER_PRICE_MAX_DIGITS
from dex_screener.handlers.hydradx.asset.asset_count import RUNTIME_BALANCE_MAX_DIGITS

if TYPE_CHECKING:
    from dipdup.models import Model


class AbstractAccount(str, ABC):
    length: int = NotImplemented
    header: str | tuple[str, ...] = NotImplemented

    @no_type_check
    def __new__(cls, address: str, **kwargs) -> AbstractAccount:
        if cls is AbstractAccount:
            raise NotImplementedError
        return str.__new__(cls, address)

    @classmethod
    def validate(cls, value: Any) -> AbstractAccount:
        if len(value) != cls.length:
            raise ValueError('Invalid length. %s must have exactly %d characters.', value, cls.length)
        if not value.startswith(cls.header):
            raise ValueError('Invalid header. %s have to start with %s.', value, cls.header)

        if value.__class__ == cls:
            return value

        raise ValueError('Invalid type %s.', type(value))


class Account(AbstractAccount):
    length: int = 66
    header: str = '0x'

    def __new__(cls, address: str, **kwargs) -> AbstractAccount:
        if cls is AbstractAccount:
            raise NotImplementedError
        try:
            return cls.validate(super().__new__(cls, address.lower(), **kwargs))
        except ValueError:
            if is_valid_ss58_address(address):
                return Account(f'{cls.header}{ss58_decode(str(address))}')
            raise


class AccountField(fields.CharField):
    __module__ = 'dipdup.fields.AccountField'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(max_length=Account.length, **kwargs)

    def to_python_value(self, value: str | None) -> Account | None:
        return Account(value) if value is not None else None

    def to_db_value(self, value: Account | str | None, instance: type[Model] | Model) -> str | None:
        if isinstance(value, Account):
            value = str(value)
        self.validate(value)
        return value


class AssetAmountField(fields.CharField):
    __module__ = 'dipdup.fields.AssetAmountField'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(max_length=RUNTIME_BALANCE_MAX_DIGITS + 1, **kwargs)


class AssetPriceField(fields.CharField):
    __module__ = 'dipdup.fields.AssetAmountField'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(max_length=DEX_SCREENER_PRICE_MAX_DIGITS + 1, **kwargs)
