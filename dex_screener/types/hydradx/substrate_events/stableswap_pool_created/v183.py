# generated by DipDup 8.2.0rc1

from __future__ import annotations

from typing import List, TypedDict


class V183(TypedDict):
    """
    A pool was created.
    """

    pool_id: int
    assets: List[int]
    amplification: int
    fee: int
