# generated by DipDup 8.2.0rc1

from __future__ import annotations

from typing import List, TypedDict


class V1002000(TypedDict):
    """
    Assets have been converted from one to another. Both `SwapExactTokenForToken`
    and `SwapTokenForExactToken` will generate this event.
    """

    who: str
    send_to: str
    amount_in: int
    amount_out: int
    path: List[List[str | int]]
