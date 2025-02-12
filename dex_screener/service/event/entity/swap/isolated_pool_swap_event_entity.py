from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO
from dex_screener.service.event.entity.swap.swap_event_entity import ClassicPoolSwapEventEntity

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent


class IsolatedPoolSwapEventEntity(ClassicPoolSwapEventEntity):
    def __init__(self, event: SubstrateEvent):
        self._event = event

    async def resolve_pool_data(self) -> SwapEventPoolDataDTO:
        return SwapEventPoolDataDTO(
            pair_id=str(self._event.payload['pool'])
            # asset_0_reserve=None,
            # asset_1_reserve=None,
        )
