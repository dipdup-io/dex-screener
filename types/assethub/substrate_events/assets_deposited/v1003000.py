# generated by DipDup 8.2.0rc1

from __future__ import annotations

from typing import TypedDict


class V1003000(TypedDict):
    """
    Some assets were deposited (e.g. for transaction fees).
    """

    asset_id: int
    who: str
    amount: int
