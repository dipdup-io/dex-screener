from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import DoesNotExist

from dex_screener import models as m
from dex_screener.types.hydradx.substrate_events.ot_c_cancelled import OTCCancelledPayload
from models.pair import upsert_pair_model


async def on_otc_cancelled(
    ctx: HandlerContext,
    event: SubstrateEvent[OTCCancelledPayload],
) -> None:
    order_id = event.payload['order_id']

    try:
        order = await m.OTCOrders.get(order_id=order_id)
    except DoesNotExist:
        error_str = f'Order not found: {order_id}, block: {event.data.header["number"]}'
        ctx.logger.error(error_str)
        return

    pair_id = await upsert_pair_model(order.asset_in, order.asset_out)

    # emit exit event
    extrinsic_index = event.data.extrinsic_index or 0
    exit_event = m.Event(
        event_type='exit',
        composite_pk=f'{event.data.block_number}-{extrinsic_index}-{event.data.index}',
        txn_id=f'{event.data.block_number}-{extrinsic_index}-{event.data.index}',
        txn_index=extrinsic_index,
        event_index=event.data.index,
        # TODO: maker is not written in order placement, current workaround is to use order_id
        maker=event.data.call_address[0] if event.data.call_address else f'Order{order.order_id}',
        pair_id=pair_id,
        # NOTE: new position contains numbers after liqudity was removed
        amount_0=order.amount_0,
        amount_1=order.amount_1,
        # FIXME: calculate priceNative
        price_native=0,
        # TODO: get and update pool fields
        # reserves_asset_0
        # reserves_asset_1
    )
    await exit_event.save()
