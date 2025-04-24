from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING

from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent


class DexScreenerEventEntity(ABC):
    event_type: str = NotImplemented

    _event: SubstrateEvent

    @abstractmethod
    def __init__(self, event: SubstrateEvent):
        raise NotImplementedError

    async def resolve_event_data(self) -> DexScreenerEventDataDTO:
        event_data: DexScreenerEventDataDTO = DexScreenerEventDataDTO(
            event_index=self._event.data.index,
            name=self._event.data.name,
            block_id=self._event.data.level,
            tx_index=self._event.data.extrinsic_index if self._event.data.extrinsic_index is not None else 0,
        )
        return event_data
