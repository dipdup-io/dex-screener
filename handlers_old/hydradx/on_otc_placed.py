from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as m
from dex_screener.types.hydradx.substrate_events.otc_placed import OTCPlacedPayload
from models.pair import upsert_pair_model


async def on_otc_placed(
    ctx: HandlerContext,
    event: SubstrateEvent[OTCPlacedPayload],
) -> None:
    order_id = event.payload['order_id']
    asset_in = event.payload['asset_in']
    asset_out = event.payload['asset_out']
    amount_in = event.payload['amount_in']
    amount_out = event.payload['amount_out']
    partially_fillable = event.payload['partially_fillable']

    # Ensure asset0 and asset1 stay the same for the same pair
    # NOTE: reversed is important because order execution record doesn't have asset_in and asset_out, only amounts
    reversed = False
    if asset_in > asset_out:
        asset_in, asset_out = asset_out, asset_in
        amount_in, amount_out = amount_out, amount_in
        reversed = True

    # save order
    order_model = m.OTCOrders(
        order_id=order_id,
        asset_in=asset_in,
        asset_out=asset_out,
        amount_in=amount_in,
        amount_out=amount_out,
        partially_fillable=partially_fillable,
        reversed=reversed,
    )
    await order_model.save()

    pair_id = await upsert_pair_model(asset_in, asset_out)

    # emit join event
    extrinsic_index = event.data.extrinsic_index or 0
    join_event = m.Event(
        event_type='join',
        composite_pk=f'{event.data.block_number}-{extrinsic_index}-{event.data.index}',
        txn_id=f'{event.data.block_number}-{extrinsic_index}-{event.data.index}',
        txn_index=extrinsic_index,
        event_index=event.data.index,
        # TODO: maker is not written in order placement, current workaround is to use order_id
        maker=event.data.call_address[0] if event.data.call_address else f'Order{order_id}',
        pair_id=pair_id,
        amount_0=amount_in,
        amount_1=amount_out,
        # TODO: calculate price?
        price_native=0,
        # TODO: get and update pool fields
        # reserves_asset_0
        # reserves_asset_1
    )
    await join_event.save()
