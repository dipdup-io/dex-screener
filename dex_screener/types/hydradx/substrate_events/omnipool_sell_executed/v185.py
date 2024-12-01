# generated by DipDup 8.1.3

from __future__ import annotations

from typing import TypedDict


class V185(TypedDict):
    """
    Sell trade executed.
    """

    who: str
    asset_in: int
    asset_out: int
    amount_in: int
    amount_out: int
    asset_fee_amount: int
    protocol_fee_amount: int
