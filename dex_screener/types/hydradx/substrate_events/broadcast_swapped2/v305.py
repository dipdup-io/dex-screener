from typing import TypedDict

from dex_screener.models.dex_fields import Account


class V305(TypedDict):
    """
    Trade executed.

    Swapped2 is a fixed and renamed version of original Swapped,
    as Swapped contained wrong input/output amounts for XYK buy trade
    """

    swapper: Account
    filler: Account
    filler_type: str
    operation: str
    inputs: list[str]
    outputs: list[str]
    fees: list[str]
    operation_stack: list[str]
