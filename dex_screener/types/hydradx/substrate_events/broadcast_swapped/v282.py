from typing import TypedDict


class V282(TypedDict):
    """
    Trade executed.
    """

    swapper: str
    filler: str
    filler_type: str
    operation: str
    inputs: list[str]
    outputs: list[str]
    fees: list[str]
    operation_stack: list[str]
