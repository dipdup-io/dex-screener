from typing import Any

from dipdup import fields


class AccountField(fields.CharField):
    __module__ = 'dipdup.fields.AccountField'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(max_length=66, **kwargs)
