# generated by DipDup 8.4.1

from __future__ import annotations

from typing import TypedDict


class V115(TypedDict):
    """
    Some balances were withdrawn (e.g. pay for transaction fee)
    """

    currency_id: int
    who: str
    amount: int
