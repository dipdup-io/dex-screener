from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import DoesNotExist

from dex_screener import models as m
from dex_screener.types.hydradx.substrate_events.otc_filled import OTCFilledPayload
from models.pair import upsert_pair_model


async def on_otc_filled(
    ctx: HandlerContext,
    event: SubstrateEvent[OTCFilledPayload],
) -> None:
    order_id = event.payload['order_id']
    who = event.payload['who']
    amount_in = event.payload['amount_in']
    amount_out = event.payload['amount_out']

    try:
        order = await m.OTCOrders.get(order_id=order_id)
    except DoesNotExist:
        error_str = f'Order not found: {order_id}, block: {event.data.header["number"]}'
        ctx.logger.error(error_str)
        return

    if order.reversed:
        amount_in, amount_out = amount_out, amount_in

    pair_id = await upsert_pair_model(order.asset_in, order.asset_out)

    # NOTE: from spec - A combination of either asset0In + asset1Out or asset1In + asset0Out is expected.
    # NOTE: opposite for sell (amounts = {'asset_1_in': amount_in, 'asset_0_out': amount_out})
    # FIXME: ensure logic is correct
    amounts = {'asset_0_in': amount_in, 'asset_1_out': amount_out}
    extrinsic_index = event.data.extrinsic_index or 0
    swap_event = m.Event(
        event_type='swap',
        composite_pk=f'{event.data.block_number}-{extrinsic_index}-{event.data.index}',
        txn_id=f'{event.data.block_number}-{extrinsic_index}-{event.data.index}',
        txn_index=extrinsic_index,
        event_index=event.data.index,
        maker=who,
        pair_id=pair_id,
        **amounts,
        # FIXME: calculate priceNative
        price_native=0,
        # TODO: get and update pool fields
        # reserves_asset_0
        # reserves_asset_1
    )
    await swap_event.save()
