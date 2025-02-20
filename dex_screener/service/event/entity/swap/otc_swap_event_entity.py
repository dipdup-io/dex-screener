from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.models import DexEvent
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.service.event.entity.swap.dto import MarketDataArgsDTO
from dex_screener.service.event.entity.swap.dto import SwapEventMarketDataDTO
from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO
from dex_screener.service.event.entity.swap.exception import InvalidSwapEventMarketDataError
from dex_screener.service.event.entity.swap.swap_event_entity import SwapEventEntity

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO


class OTCSwapEventEntity(SwapEventEntity):
    _pair: Pair

    def __init__(self, event: SubstrateEvent):
        self._event = event

    async def resolve(self):
        return await super().resolve()

    async def resolve_event_data(self) -> DexScreenerEventDataDTO:
        return await super().resolve_event_data()

    async def resolve_pool_data(self) -> SwapEventPoolDataDTO:
        match self._event.payload:
            case {
                'order_id': int(order_id),
            }:
                order = await Pool.get(dex_key=DexKey.OTC, dex_pool_id=order_id)
                self._pair = await Pair.get(
                    pool=order,
                    dex_key=DexKey.OTC,
                )

            case _:
                raise RuntimeError(self._event.payload)

        return SwapEventPoolDataDTO(
            pair_id=self._pair.id,
        )

    async def resolve_market_data(self) -> SwapEventMarketDataDTO:
        await self._pair.fetch_related('asset_0', 'asset_1')
        match self._event.payload:
            case {
                'who': str(maker),
                'amount_in': int(minor_amount_in),
                'amount_out': int(minor_amount_out),
            }:
                pass
            case _:
                raise InvalidSwapEventMarketDataError(f'Unhandled Swap Event Payload: {self._event.payload}.')
        resolved_args = MarketDataArgsDTO(
            maker=maker,
            asset_in_id=self._pair.asset_0.id if self._pair.id[-9]=='0' else self._pair.asset_1.id,
            asset_out_id=self._pair.asset_0.id if self._pair.id[-9]=='1' else self._pair.asset_1.id,
            minor_amount_in=int(minor_amount_in),
            minor_amount_out=int(minor_amount_out),
        )
        return await self._market_data_from_args(resolved_args)

    async def save(self) -> DexEvent:
        return await super().save()
