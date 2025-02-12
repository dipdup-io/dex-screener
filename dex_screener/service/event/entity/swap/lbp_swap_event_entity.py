from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO
from dex_screener.service.event.entity.swap.swap_event_entity import ClassicPoolSwapEventEntity

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent


class LBPSwapEventEntity(ClassicPoolSwapEventEntity):
    def __init__(self, event: SubstrateEvent):
        self._event = event

    async def resolve_pool_data(self) -> SwapEventPoolDataDTO:
        asset_a_id = self._event.payload['asset_in']
        asset_b_id = self._event.payload['asset_out']
        pair = await Pair.filter(
            dex_key=DexKey.LBP,
            asset_0_id=min(asset_a_id, asset_b_id),
            asset_1_id=max(asset_a_id, asset_b_id),
        ).first()
        return SwapEventPoolDataDTO(
            pair_id=pair.id,
            # asset_0_reserve=None,
            # asset_1_reserve=None,
        )
