from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.service.dex.otc.const import MOCK_OTC_ORDER_ACCOUNT

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.types.hydradx.substrate_events.otc_placed import OTCPlacedPayload


class OTCService:
    logger = logging.getLogger('otc_service')

    @classmethod
    def get_order_account(cls, order_id: int, asset_in_id: int, asset_out_id: int) -> str:
        order_account: str = ''.join(
            [
                MOCK_OTC_ORDER_ACCOUNT[:-9],
                str(int(asset_in_id > asset_out_id)),
                int.to_bytes(order_id, 4).hex(),
            ]
        )

        return order_account

    @classmethod
    async def register_order(cls, event: SubstrateEvent[OTCPlacedPayload]) -> Pool:
        match event.payload:
            case {
                'order_id': int(order_id),
                'asset_in': int(asset_in_id),
                'asset_out': int(asset_out_id),
            }:
                pass
            case _:
                raise RuntimeError

        order = await Pool.create(
            account=cls.get_order_account(order_id, asset_in_id, asset_out_id),
            dex_key=DexKey.OTC,
            dex_pool_id=order_id,
            shares='0',
        )
        cls.logger.info('Order registered: %r.', order)

        pair_id = order.account
        event_info = DexScreenerEventInfoDTO.from_event(event)
        pair = await Pair.create(
            id=pair_id,
            dex_key=order.dex_key,
            asset_0_id=min(asset_in_id, asset_out_id),
            asset_1_id=max(asset_in_id, asset_out_id),
            pool=order,
            created_at_block_id=event_info.block_id,
            created_at_tx_id=event_info.tx_index,
        )
        cls.logger.info('Pair registered in pool %r: %r.', order, pair)

        await pair.fetch_related('asset_0', 'asset_1')
        await order.assets.add(pair.asset_0, pair.asset_1)  # type: ignore[attr-defined]

        return order
