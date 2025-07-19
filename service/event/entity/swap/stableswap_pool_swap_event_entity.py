from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.models import DexEvent
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.service.dex.stableswap.stableswap_service import get_pair_id
from dex_screener.service.event.entity.swap.dto import SwapEventMarketDataDTO
from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO
from dex_screener.service.event.entity.swap.resolve_helper import MultiAssetPoolSwapEventMarketDataHelper
from dex_screener.service.event.entity.swap.swap_event_entity import SwapEventEntity
from dex_screener.utils import get_balance_by_account

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO


class StableSwapPoolSwapEventEntity(SwapEventEntity):
    def __init__(self, event: SubstrateEvent):
        self._event = event

    async def resolve(self):
        return await super().resolve()

    async def resolve_event_data(self) -> DexScreenerEventDataDTO:
        return await super().resolve_event_data()

    async def resolve_pool_data(self) -> SwapEventPoolDataDTO:
        pool = await Pool.get(
            dex_key=DexKey.StableSwap,
            lp_token_id=int(self._event.payload['pool_id']),
        )

        pair_id = get_pair_id(
            pool=pool,
            asset_a_id=self._event.payload['asset_in'],
            asset_b_id=self._event.payload['asset_out'],
        )

        pair = await Pair.get(id=pair_id)
        reserves_0 = await get_balance_by_account(pair.pool.account, pair.asset_0.id, self._event.data.level)
        reserves_1 = await get_balance_by_account(pair.pool.account, pair.asset_1.id, self._event.data.level)
        return SwapEventPoolDataDTO(
            pair_id=pair_id,
            asset_0_reserve=reserves_0,
            asset_1_reserve=reserves_1,
        )

    async def resolve_market_data(self) -> SwapEventMarketDataDTO:
        resolved_args = await MultiAssetPoolSwapEventMarketDataHelper.extract_args_from_payload(self._event.payload)
        return await self._market_data_from_args(resolved_args)

    async def save(self) -> DexEvent:
        return await super().save()
