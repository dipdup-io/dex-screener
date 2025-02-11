from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.service.event.entity.swap.dto import MarketDataArgsDTO
from dex_screener.service.event.entity.swap.dto import SwapEventMarketDataDTO
from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO
from dex_screener.service.event.entity.swap.exception import InvalidSwapEventMarketDataError
from dex_screener.service.event.entity.swap.swap_event_entity import SwapEventEntity

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent


class LBPSwapEventEntity(SwapEventEntity):
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

    async def resolve_market_data(self) -> SwapEventMarketDataDTO:
        match self._event.payload:
            case {
                'who': str(maker),
                'asset_in': int(asset_in_id),
                'asset_out': int(asset_out_id),
                'buy_price': int(minor_amount_in),
                'amount': int(minor_amount_out),
            }:
                pass
            case {
                'who': str(maker),
                'asset_in': int(asset_in_id),
                'asset_out': int(asset_out_id),
                'sale_price': int(minor_amount_out),
                'amount': int(minor_amount_in),
            }:
                pass
            case _:
                raise InvalidSwapEventMarketDataError(f'Unhandled LBP Swap Event Payload: {self._event.payload}.')

        resolved_args = MarketDataArgsDTO(
            maker=maker,
            asset_in_id=asset_in_id,
            asset_out_id=asset_out_id,
            minor_amount_in=minor_amount_in,
            minor_amount_out=minor_amount_out,
        )

        return await self._market_data_from_args(resolved_args)
