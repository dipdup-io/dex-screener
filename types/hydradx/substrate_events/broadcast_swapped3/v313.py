from typing import TypedDict

from dex_screener.models.dex_fields import Account


class V313(TypedDict):
    """
    Trade executed.

    Swapped3 is a fixed and renamed version of original Swapped,
    as Swapped contained wrong input/output amounts for XYK buy trade

    Swapped3 is a fixed and renamed version of original Swapped3,
    as Swapped contained wrong filler account on AAVE trades
    """

    swapper: Account
    filler: Account
    filler_type: str
    operation: str
    inputs: list[str]
    outputs: list[str]
    fees: list[str]
    operation_stack: list[str]
