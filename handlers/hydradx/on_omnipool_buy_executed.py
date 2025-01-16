from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as m
from dex_screener.types.hydradx.substrate_events.omnipool_buy_executed import OmnipoolBuyExecutedPayload


async def on_omnipool_buy_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolBuyExecutedPayload],
) -> None:
    who = event.payload['who']
    asset_in = event.payload['asset_in']
    asset_out = event.payload['asset_out']
    amount_in = event.payload['amount_in']
    amount_out = event.payload['amount_out']

    # pair should remain the same, asset0 and asset1 should stay the same
    if asset_in > asset_out:
        asset_in, asset_out = asset_out, asset_in
        amount_in, amount_out = amount_out, amount_in

    # TODO: refactor
    pair_id = m.get_pair_id(asset_in, asset_out)
    await update_pair_model(pair_id, asset_in, asset_out)

    # NOTE: from spec - A combination of either asset0In + asset1Out or asset1In + asset0Out is expected.
    # NOTE: opposite for sell (amounts = {'asset_1_in': amount_in, 'asset_0_out': amount_out})
    amounts = {'asset_0_in': amount_in, 'asset_1_out': amount_out}
    event_model = m.SwapEvent(
        event_type='swap',
        composite_pk=f'{event.data.block_number}-{event.data.extrinsic_index}-{event.data.index}',
        # NOTE: take caution, event index is used due to extrinsic index being null
        txn_id=f'{event.data.block_number}-{event.data.extrinsic_index}-{event.data.index}',
        txn_index=event.data.extrinsic_index or event.data.index,
        event_index=event.data.index,
        maker=who,
        pair_id=pair_id,
        # TODO: get and update pool fields
        # reserves_asset_0
        # reserves_asset_1
        **amounts,
        # FIXME: calculate priceNative
        price_native=0,
    )

    await event_model.save()


async def update_pair_model(pair_id, asset0_id, asset1_id) -> str:
    # FIXME: ensure pair data is correct and full
    pair_model, created = await m.Pair.get_or_create(
        id=pair_id, defaults={'asset_0_id': asset0_id, 'asset_1_id': asset1_id, 'dex_key': 'hydradx'}
    )
    if not created:
        await pair_model.save()
