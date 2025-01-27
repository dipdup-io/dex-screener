from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import DoesNotExist

from dex_screener.models import Asset
from dex_screener.models import SwapEvent
from dex_screener.types.hydradx.substrate_events.xyk_buy_executed import XYKBuyExecutedPayload


async def on_buy_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKBuyExecutedPayload],
) -> None:
    try:
        asset_in = await Asset.get(id=event.payload['asset_in'])
        assert asset_in.decimals is not None
        asset_out = await Asset.get(id=event.payload['asset_out'])
        assert asset_out.decimals is not None
    except (DoesNotExist, AssertionError):
        return

    await SwapEvent.create(
        txn_id=event.data.header['hash'],
        txn_index=event.data.extrinsic_index,
        event_index=event.data.index,
        maker=event.payload['who'],
        pair_id=event.payload['pool'],
        asset_in_id=asset_in.id,
        asset_out_id=asset_out.id,
        amount_in=event.payload['amount'] / 10**asset_in.decimals,
        direction=False,
        price=event.payload['buy_price'],
        created_at_block_id=event.level,
    )
