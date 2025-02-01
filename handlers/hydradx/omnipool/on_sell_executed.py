from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import DoesNotExist

from dex_screener.models import Asset
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import SwapEvent
from dex_screener.models import get_composite_key
from dex_screener.types.hydradx.substrate_events.omnipool_sell_executed import OmnipoolSellExecutedPayload
from models import get_pair_id


async def on_sell_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolSellExecutedPayload],
) -> None:
    try:
        asset_in = await Asset.get(id=event.payload['asset_in'])
        assert asset_in.decimals is not None
        asset_out = await Asset.get(id=event.payload['asset_out'])
        assert asset_out.decimals is not None

        pair, _ = await Pair.get_or_create(
            id=get_pair_id(asset_in.id, asset_out.id),
            defaults={
                'dex_key': DexKey.hydradx_omnipool,
                'asset_0_id': min(asset_in.id, asset_out.id),
                'asset_1_id': max(asset_in.id, asset_out.id),
                'created_at_txn_id': get_composite_key(event.data),
                'created_at_block_number': event.level,
            },
        )
    except (DoesNotExist, AssertionError):
        raise

    amount_in = event.payload['amount_in'] / 10**asset_in.decimals
    amount_out = event.payload['amount_out'] / 10**asset_out.decimals
    await SwapEvent.create(
        txn_id=event.data.header['hash'],
        txn_index=event.data.extrinsic_index,
        event_index=event.data.index,
        maker=event.payload['who'],
        pair_id=pair.id,
        asset_in_id=asset_in.id,
        asset_out_id=asset_out.id,
        amount_in=amount_in,
        amount_out=amount_out,
        direction=True,
        price=amount_out / amount_in,
        created_at_block_number=event.level,
    )
