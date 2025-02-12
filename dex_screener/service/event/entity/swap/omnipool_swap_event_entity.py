from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.service.dex.omnipool.omnipool_service import OmnipoolService
from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO
from dex_screener.service.event.entity.swap.swap_event_entity import MultiAssetPoolSwapEventEntity

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent


class OmnipoolSwapEventEntity(MultiAssetPoolSwapEventEntity):
    def __init__(self, event: SubstrateEvent):
        self._event = event

    async def resolve_pool_data(self) -> SwapEventPoolDataDTO:
        return SwapEventPoolDataDTO(
            pair_id=OmnipoolService.get_pair_id(self._event.payload['asset_in'], self._event.payload['asset_out']),
            # asset_0_reserve=None,
            # asset_1_reserve=None,
        )
