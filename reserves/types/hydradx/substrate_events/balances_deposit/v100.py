# generated by DipDup 8.4.1

from __future__ import annotations

from typing import TypedDict


class V100(TypedDict):
    """
    Some amount was deposited into the account (e.g. for transaction fees). [who,
    deposit]
    """

    who: str
    deposit: int
