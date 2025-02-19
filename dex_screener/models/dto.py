from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self

from pydantic import BaseModel

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent


class DexScreenerEventInfoDTO(BaseModel):
    event_index: int
    name: str
    block_id: int
    tx_index: int

    @classmethod
    def from_event(cls, event: SubstrateEvent) -> Self:
        return cls(
            event_index=event.data.index,
            name=event.name,
            block_id=event.level,
            tx_index=cls._get_tx_index(event),
        )

    @classmethod
    def _get_tx_index(cls, event: SubstrateEvent) -> int:
        if event.data.extrinsic_index is not None:
            return event.data.extrinsic_index
        return 0

    def get_explorer_url(self) -> str:
        return f'https://hydration.subscan.io/block/{self.block_id}?tab=event&event={self.block_id}-{self.event_index}'
