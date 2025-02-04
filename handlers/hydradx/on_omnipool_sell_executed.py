from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as m
from dex_screener.types.hydradx.substrate_events.omnipool_sell_executed import OmnipoolSellExecutedPayload
from models.pair import upsert_pair_model


async def on_omnipool_sell_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolSellExecutedPayload],
) -> None:
    who = event.payload['who']
    asset_in = event.payload['asset_in']
    asset_out = event.payload['asset_out']
    amount_in = event.payload['amount_in']
    amount_out = event.payload['amount_out']

    # Ensure asset0 and asset1 stay the same for the same pair
    if asset_in > asset_out:
        asset_in, asset_out = asset_out, asset_in
        amount_in, amount_out = amount_out, amount_in

    pair_id = await upsert_pair_model(asset_in, asset_out)

    # NOTE: from spec - A combination of either asset0In + asset1Out or asset1In + asset0Out is expected.
    amounts = {'asset_1_in': amount_in, 'asset_0_out': amount_out}
    extrinsic_index = event.data.extrinsic_index or 0
    event_model = m.Event(
        event_type='swap',
        composite_pk=f'{event.data.block_number}-{extrinsic_index}-{event.data.index}',
        # NOTE: take caution, event index is used due to extrinsic index being null
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

    await event_model.save()
