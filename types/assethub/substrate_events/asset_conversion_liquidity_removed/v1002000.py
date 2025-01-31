# generated by DipDup 8.2.0rc1

from __future__ import annotations

from typing import List, TypedDict


class V1002000(TypedDict):
    """
    A successful call of the `RemoveLiquidity` extrinsic will create this event.
    """

    who: str
    withdraw_to: str
    pool_id: List[str]
    amount1: int
    amount2: int
    lp_token: int
    lp_token_burned: int
    withdrawal_fee: int
