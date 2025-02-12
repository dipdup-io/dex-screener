from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.service.event.entity.swap.dto import SwapEventMarketDataDTO
from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO
from dex_screener.service.event.entity.swap.resolve_helper import ClassicPoolSwapEventMarketDataHelper
from dex_screener.service.event.entity.swap.swap_event_entity import SwapEventEntity

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.models import SwapEvent
    from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO


class IsolatedPoolSwapEventEntity(SwapEventEntity):
    def __init__(self, event: SubstrateEvent):
        self._event = event

    async def resolve(self):
        return await super().resolve()

    async def resolve_event_data(self) -> DexScreenerEventDataDTO:
        return await super().resolve_event_data()

    async def resolve_pool_data(self) -> SwapEventPoolDataDTO:
        return SwapEventPoolDataDTO(
            pair_id=str(self._event.payload['pool'])
            # asset_0_reserve=None,
            # asset_1_reserve=None,
        )

    async def resolve_market_data(self) -> SwapEventMarketDataDTO:
        resolved_args = await ClassicPoolSwapEventMarketDataHelper.extract_args_from_payload(self._event.payload)
        return await self._market_data_from_args(resolved_args)

    async def save(self) -> SwapEvent:
        return await super().save()
