from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.models import DexKey
from dex_screener.models import Pool
from dex_screener.service.dex.stableswap.stableswap_service import StableSwapService
from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO
from dex_screener.service.event.entity.swap.swap_event_entity import MultiAssetPoolSwapEventEntity

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent


class StableSwapPoolSwapEventEntity(MultiAssetPoolSwapEventEntity):
    def __init__(self, event: SubstrateEvent):
        self._event = event

    async def resolve_pool_data(self) -> SwapEventPoolDataDTO:
        pool = await Pool.get(
            dex_key=DexKey.StableSwap,
            dex_pool_id=str(self._event.payload['pool_id']),
        )

        pair_id = StableSwapService.get_pair_id(
            pool_account=pool.account,
            asset_a_id=self._event.payload['asset_in'],
            asset_b_id=self._event.payload['asset_out'],
        )

        return SwapEventPoolDataDTO(
            pair_id=pair_id,
            # asset_0_reserve=None,
            # asset_1_reserve=None,
        )
