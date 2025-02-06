import logging

from dipdup.models.substrate import SubstrateEvent

from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError
from dex_screener.models import Asset
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models import SwapEvent
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.service.dex.isolated_pool.const import XYK_GET_EXCHANGE_FEE_BPS
from dex_screener.types.hydradx.substrate_events.xyk_buy_executed import XYKBuyExecutedPayload
from dex_screener.types.hydradx.substrate_events.xyk_pool_created import XYKPoolCreatedPayload
from dex_screener.types.hydradx.substrate_events.xyk_sell_executed import XYKSellExecutedPayload


class IsolatedPoolService:
    logger = logging.getLogger('isolated_pool_service')

    @classmethod
    async def register_pool(cls, event: SubstrateEvent[XYKPoolCreatedPayload]):
        pool, _ = await Pool.update_or_create(
            id=event.payload['pool'],
            defaults={
                'account': event.payload['pool'],
                'dex_key': DexKey.IsolatedPool,
                'lp_token_id': event.payload['share_token'],
            },
        )
        cls.logger.info('Pool registered: %r.', pool)

        return pool

    @classmethod
    async def register_pair(cls, pool: Pool, event: SubstrateEvent[XYKPoolCreatedPayload]):
        pair_id = pool.account
        if await Pair.exists(id=pair_id):
            cls.logger.warning('Pair already exists: %s.', pair_id)
            return

        asset_a = await Asset.get(id=event.payload['asset_a'])
        asset_b = await Asset.get(id=event.payload['asset_b'])
        event_info = DexScreenerEventInfoDTO.from_event(event)

        pair = await Pair.create(
            id=pair_id,
            dex_key=DexKey.IsolatedPool,
            asset_0_id=min(asset_a.id, asset_b.id),
            asset_1_id=max(asset_a.id, asset_b.id),
            pool=pool,
            created_at_block_id=event_info.block_id,
            created_at_txn_id=event_info.tx_id,
            fee_bps=XYK_GET_EXCHANGE_FEE_BPS,
        )
        cls.logger.info('Pair registered in pool %r: %r.', pool, pair)

        await pool.assets.add(asset_a, asset_b)
        cls.logger.info('Pair Assets added to pool %r: %s, %s.', pool, asset_a, asset_b)

    @classmethod
    async def register_swap(cls, event: SubstrateEvent[XYKBuyExecutedPayload | XYKSellExecutedPayload]):
        asset_in: Asset = await Asset.get(id=event.payload['asset_in'])
        asset_out: Asset = await Asset.get(id=event.payload['asset_out'])

        match event:
            case SubstrateEvent(
                name='XYK.BuyExecuted',
                payload={
                    'buy_price': int(minor_amount_in),
                    'amount': int(minor_amount_out),
                },
            ):
                pass

            case SubstrateEvent(
                name='XYK.SellExecuted',
                payload={
                    'sale_price': int(minor_amount_out),
                    'amount': int(minor_amount_in),
                },
            ):
                pass

            case _:
                raise InvalidEventDataError(f'Unhandled XYK Swap Event: {event}.')

        asset_amount_in = asset_in.from_minor(minor_amount_in)
        asset_amount_out = asset_out.from_minor(minor_amount_out)

        if asset_in.id < asset_out.id:
            swap_data = {
                'amount_0_in': asset_amount_in,
                'amount_1_out': asset_amount_out,
                'price': asset_amount_out / asset_amount_in,
            }
        else:
            swap_data = {
                'amount_0_out': asset_amount_out,
                'amount_1_in': asset_amount_in,
                'price': asset_amount_in / asset_amount_out,
            }

        swap_data.update(
            {
                'maker': event.payload['who'],
                'pair_id': event.payload['pool'],
                'event_type': 'swap',
            }
        )

        event_info = DexScreenerEventInfoDTO.from_event(event)

        metadata = {
            'explorer': event_info.get_explorer_url(),
            'market data': {
                'maker pay': f'{asset_amount_in!r}',
                'maker get': f'{asset_amount_out!r}',
                'market pair': f'{asset_amount_out.asset}/{asset_amount_in.asset}',
                'market price expression': f'{asset_amount_in!r} / {asset_amount_out!r}',
                'market price': f'{(asset_amount_in/asset_amount_out)!r}',
            },
            'dex-screener data': {
                'fixed pair': f'{swap_data['price'].pair!s}',
                'native price': f'{swap_data['price']!r}',
            },
        }

        swap = await SwapEvent.create(
            **event_info.model_dump(),
            **swap_data,
            metadata=metadata,
        )
        cls.logger.info('Swap Event %s registered: %s [%s].', event_info.name, swap.id, event_info.get_explorer_url())

        # await event_info.update_latest_block()
