from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.service.event.entity.swap.isolated_pool_swap_event_entity import IsolatedPoolSwapEventEntity
from dex_screener.service.event.entity.swap.lbp_swap_event_entity import LBPSwapEventEntity
from dex_screener.service.event.entity.swap.omnipool_swap_event_entity import OmnipoolSwapEventEntity
from dex_screener.service.event.entity.swap.otc_swap_event_entity import OTCSwapEventEntity
from dex_screener.service.event.entity.swap.stableswap_pool_swap_event_entity import StableSwapPoolSwapEventEntity
from dex_screener.service.event.entity.swap.unified_trade_event_entity import UnifiedTradeEventEntity

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.models import DexEvent
    from dex_screener.service.event.entity.swap.swap_event_entity import SwapEventEntity


class DexScreenerEventService:
    @classmethod
    async def register_swap(cls, event: SubstrateEvent) -> DexEvent:
        swap_event: SwapEventEntity = cls.build_swap_event_entity(event)
        await swap_event.resolve()
        return await swap_event.save()

    @classmethod
    def build_swap_event_entity(cls, event: SubstrateEvent) -> SwapEventEntity | None:
        match event.data.name:
            case 'Omnipool.BuyExecuted' | 'Omnipool.SellExecuted':
                return OmnipoolSwapEventEntity(event)
            case 'Stableswap.BuyExecuted' | 'Stableswap.SellExecuted':
                return StableSwapPoolSwapEventEntity(event)
            case 'XYK.BuyExecuted' | 'XYK.SellExecuted':
                return IsolatedPoolSwapEventEntity(event)
            case 'LBP.BuyExecuted' | 'LBP.SellExecuted':
                return LBPSwapEventEntity(event)
            case 'OTC.Filled' | 'OTC.PartiallyFilled':
                return OTCSwapEventEntity(event)
            case 'Broadcast.Swapped' | 'Broadcast.Swapped2' | 'Broadcast.Swapped3':
                return UnifiedTradeEventEntity(event)

    @classmethod
    async def register_join_exit(cls, event): ...
