from typing import TypedDict

from dex_screener.models.dex_fields import Account


class V282(TypedDict):
    """
    Trade executed.
    """

    swapper: Account
    filler: Account
    filler_type: str
    operation: str
    inputs: list[str]
    outputs: list[str]
    fees: list[str]
    operation_stack: list[str]
