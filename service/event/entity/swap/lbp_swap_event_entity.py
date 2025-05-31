from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.models import DexEvent
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.service.event.entity.swap.dto import SwapEventMarketDataDTO
from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO
from dex_screener.service.event.entity.swap.resolve_helper import ClassicPoolSwapEventMarketDataHelper
from dex_screener.service.event.entity.swap.swap_event_entity import SwapEventEntity

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO


class LBPSwapEventEntity(SwapEventEntity):
    def __init__(self, event: SubstrateEvent):
        self._event = event

    async def resolve(self):
        return await super().resolve()

    async def resolve_event_data(self) -> DexScreenerEventDataDTO:
        return await super().resolve_event_data()

    async def resolve_pool_data(self) -> SwapEventPoolDataDTO:
        asset_a_id = self._event.payload['asset_in']
        asset_b_id = self._event.payload['asset_out']
        pair = await Pair.filter(
            dex_key=DexKey.LBP,
            asset_0_id=min(asset_a_id, asset_b_id),
            asset_1_id=max(asset_a_id, asset_b_id),
        ).first()
        asset_0_reserve, asset_1_reserve = await pair.get_reserves()  # type: ignore[union-attr]
        return SwapEventPoolDataDTO(
            pair_id=pair.id,  # type: ignore[union-attr]
            asset_0_reserve=asset_0_reserve,
            asset_1_reserve=asset_1_reserve,
        )

    async def resolve_market_data(self) -> SwapEventMarketDataDTO:
        resolved_args = await ClassicPoolSwapEventMarketDataHelper.extract_args_from_payload(self._event.payload)
        return await self._market_data_from_args(resolved_args)

    async def save(self) -> DexEvent:
        return await super().save()
