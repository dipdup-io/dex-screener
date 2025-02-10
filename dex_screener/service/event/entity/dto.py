from typing import Annotated

from pydantic import BaseModel
from pydantic import Field
from pydantic import computed_field


class DexScreenerEventDataDTO(BaseModel):
    id: Annotated[int, Field(exclude=True)]
    name: str
    block_id: int
    tx_index: int

    @computed_field
    @property
    def tx_id(self) -> str:
        return f'{self.block_id}-{self.tx_index}'

    @computed_field
    @property
    def event_index(self) -> str:
        return f'{self.block_id}-{self.id}'
