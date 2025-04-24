from __future__ import annotations

from typing import TYPE_CHECKING

from scalecodec import is_valid_ss58_address
from scalecodec import ss58_decode

from dex_screener.models import DexEvent
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.service.event.entity.swap.dto import MarketDataArgsDTO
from dex_screener.service.event.entity.swap.dto import SwapEventMarketDataDTO
from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO
from dex_screener.service.event.entity.swap.exception import InvalidSwapEventMarketDataError
from dex_screener.service.event.entity.swap.swap_event_entity import SwapEventEntity

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO


class UnifiedTradeEventEntity(SwapEventEntity):
    def __init__(self, event: SubstrateEvent):
        self._event = event

    async def resolve(self):
        return await super().resolve()

    async def resolve_event_data(self) -> DexScreenerEventDataDTO:
        return await super().resolve_event_data()

    async def resolve_pool_data(self) -> SwapEventPoolDataDTO:
        match self._event.payload:
            case {
                'filler_type': {'XYK': int(lp_token_id)},
            }:
                pair = await Pair.get(
                    pool__dex_key=DexKey.IsolatedPool,
                    pool__lp_token_id=lp_token_id,
                )
            case {
                'filler_type': {'OTC': int(otc_order_id)},
            }:
                pair = await Pair.get(
                    pool__dex_key=DexKey.OTC,
                    pool__dex_pool_id=otc_order_id,
                )
            case {
                'filler_type': {'Stableswap': int(stableswap_pool_id)},
                'inputs': ({'asset': int(asset_a_id)},),
                'outputs': ({'asset': int(asset_b_id)},),
            }:
                pair = await Pair.get(
                    pool__dex_key=DexKey.StableSwap,
                    pool__dex_pool_id=stableswap_pool_id,
                    asset_0_id=min(asset_a_id, asset_b_id),
                    asset_1_id=max(asset_a_id, asset_b_id),
                )
            case {
                'filler_type': 'Omnipool',
                'inputs': ({'asset': int(asset_a_id)},),
                'outputs': ({'asset': int(asset_b_id)},),
            }:
                pair = await Pair.get(
                    pool__dex_key=DexKey.Omnipool,
                    asset_0_id=min(asset_a_id, asset_b_id),
                    asset_1_id=max(asset_a_id, asset_b_id),
                )
            case {
                'filler': str(pool_account),
                'inputs': ({'asset': int(asset_a_id)},),
                'outputs': ({'asset': int(asset_b_id)},),
            }:
                pair = await Pair.get(
                    pool_id=pool_account,
                    asset_0_id=min(asset_a_id, asset_b_id),
                    asset_1_id=max(asset_a_id, asset_b_id),
                )

            case _:
                raise RuntimeError(self._event.payload)

        asset_0_reserve, asset_1_reserve = await pair.get_reserves()

        return SwapEventPoolDataDTO(
            pair_id=pair.id,
            asset_0_reserve=asset_0_reserve,
            asset_1_reserve=asset_1_reserve,
        )

    async def resolve_market_data(self) -> SwapEventMarketDataDTO:
        match self._event.payload:
            case {
                'swapper': str(maker),
                'inputs': ({'asset': int(asset_in_id), 'amount': minor_amount_in},),
                'outputs': ({'asset': int(asset_out_id), 'amount': minor_amount_out},),
            }:
                if is_valid_ss58_address(maker):
                    maker = '0x' + ss58_decode(maker)

                pass
            case _:
                raise InvalidSwapEventMarketDataError(f'Unhandled Swap Event Payload: {self._event.payload}.')
        resolved_args = MarketDataArgsDTO(
            maker=maker,
            asset_in_id=asset_in_id,
            asset_out_id=asset_out_id,
            minor_amount_in=int(minor_amount_in),
            minor_amount_out=int(minor_amount_out),
        )
        return await self._market_data_from_args(resolved_args)

    async def save(self) -> DexEvent:
        return await super().save()
