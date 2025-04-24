from typing import Self

from pydantic import BaseModel
from pydantic import model_validator


class SwapEventPoolDataDTO(BaseModel):
    pair_id: str
    asset_0_reserve: str | None = None
    asset_1_reserve: str | None = None


class SwapEventMarketDataDTO(BaseModel):
    maker: str
    amount_0_in: str | None = None
    amount_1_in: str | None = None
    amount_0_out: str | None = None
    amount_1_out: str | None = None
    price: str


class MarketDataArgsDTO(BaseModel):
    maker: str
    asset_in_id: int
    asset_out_id: int
    minor_amount_in: int
    minor_amount_out: int

    @model_validator(mode='after')
    def check_amounts(self) -> Self:
        if self.minor_amount_in * self.minor_amount_out == 0:
            raise ValueError(f'Amount must be positive int: {self!r}.')
        return self
