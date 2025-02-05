from typing import Annotated
from typing import Self

from dipdup.models.substrate import SubstrateEvent
from pydantic import BaseModel
from pydantic import Field
from pydantic import computed_field


class DexScreenerEventInfoDTO(BaseModel):
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

    @classmethod
    def from_event(cls, event: SubstrateEvent) -> Self:
        return cls(
            id=event.data.index,
            name=event.name,
            block_id=event.level,
            tx_index=cls._get_tx_index(event),
        )

    @classmethod
    def _get_tx_index(cls, event: SubstrateEvent) -> int:
        if event.data.extrinsic_index is not None:
            return event.data.extrinsic_index
        return 0

    async def update_latest_block(self):
        from dex_screener.models import Block
        from dex_screener.models import LatestBlock
        block = await Block.get(level=self.block_id)

        await LatestBlock.update_or_create(
            id=True,
            defaults={'block_number': block.level, 'block_timestamp': block.timestamp},
        )
