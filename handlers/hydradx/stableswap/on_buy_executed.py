from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import DoesNotExist

from dex_screener import models as m
from dex_screener.types.hydradx.substrate_events.stableswap_buy_executed import StableswapBuyExecutedPayload
from models.pair import upsert_pair_model


async def on_buy_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapBuyExecutedPayload],
) -> None:
    asset_in = event.payload['asset_in']
    asset_out = event.payload['asset_out']
    amount_in = event.payload['amount_in']
    amount_out = event.payload['amount_out']

    # Ensure asset0 and asset1 stay the same for the same pair
    if asset_in > asset_out:
        asset_in, asset_out = asset_out, asset_in
        amount_in, amount_out = amount_out, amount_in

    try:
        asset_0_obj: m.Asset = await m.Asset.get(id=asset_in)
        asset_1_obj: m.Asset = await m.Asset.get(id=asset_out)

        asset_in_decimals = asset_0_obj.decimals
        asset_out_decimals = asset_1_obj.decimals
    except DoesNotExist:
        error_str = f'Asset not found: {asset_in}, {asset_out}'
        ctx.logger.error(error_str)

    # TODO: REMOVE, workaround because hydradx decimals are nowhere to be found atm
    asset_in_decimals = asset_in_decimals or 6
    asset_out_decimals = asset_out_decimals or 6

    pair_id = await upsert_pair_model(asset_in, asset_out, m.DexKey.hydradx_omnipool)

    amount_in = event.payload['amount_in'] / 10**asset_out_decimals
    amount_out = event.payload['amount_out'] / 10**asset_out_decimals
    await m.SwapEvent.create(
        txn_id=event.data.header['hash'],
        txn_index=event.data.extrinsic_index,
        event_index=event.data.index,
        maker=event.payload['who'],
        pair_id=pair_id,
        asset_in_id=asset_in,
        asset_out_id=asset_out,
        # TODO: after model fix replace with amounts = {'asset_0_in': amount_in, 'asset_1_out': amount_out}
        amount_in=amount_in,
        amount_out=amount_out,
        direction=False,
        price=amount_out / amount_in,
        created_at_block_id=event.level,
    )
