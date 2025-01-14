from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as m
from dex_screener.types.hydradx.substrate_events.stableswap_sell_executed import StableswapSellExecutedPayload


async def on_sell_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapSellExecutedPayload],
) -> None:
    # await Event.create(
    #     who=event.data.args['who'],
    #     asset_in=event.data.args['assetIn'],
    #     asset_out=event.data.args['assetOut'],
    #     amount_in=event.data.args['amountIn'],
    #     amount_out=event.data.args['amountOut'],
    # )

    asset0_id = min(event.data.args['assetIn'], event.data.args['assetOut'])
    asset1_id = max(event.data.args['assetIn'], event.data.args['assetOut'])

    asset0_model = await m.Asset.filter(id=asset0_id).get()
    asset1_model = await m.Asset.filter(id=asset1_id).get()

    pair_id = m.get_pair_id(asset0_id, asset1_id)
    pair_model, created = m.Pair.get_or_create(
        id=pair_id, defaults={'asset_0_id': asset0_id, 'asset_1_id': asset1_id, 'dex_key': 'hydradx'}  # ?
    )
    if not created:
        await pair_model.save()

    # TODO: find or create pool

    event_model = m.SwapEvent(
        event_type='swap',
        txn_id=event.data.header.extrinsicsRoot,  # ?
        txn_index=event.data.extrinsic_index,  # ?
        event_index=event.data.index,
        maker=event.payload['who'],
        pair_id=pair_id,
        # asset_0_in=fields.IntField(null=True)
        # asset_1_in=fields.IntField(null=True)
        # asset_0_out=fields.IntField(null=True)
        # asset_1_out=fields.IntField(null=True)
        # NOTE: where?
        # price_native=fields.IntField()
        # NOTE: optionals:
        # reserves_asset_0=fields.IntField(null=True)
        # reserves_asset_1=fields.IntField(null=True)
        # metadata=fields.JSONField(null=True)
    )
    await event_model.save()
