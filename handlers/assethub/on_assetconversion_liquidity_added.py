from decimal import Decimal

from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models
from dex_screener.types.assethub.substrate_events.asset_conversion_liquidity_added import (
    AssetConversionLiquidityAddedPayload,
)


async def on_assetconversion_liquidity_added(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionLiquidityAddedPayload],
) -> None:
    pool_id = models.get_pool_id(event.payload)
    if not pool_id:
        return

    pool = await models.Pool.get(id=pool_id)
    ctx.logger.info('Liquidity added to pool `%s`', pool.id)

    # position_id = event.payload['position_id']
    # owner = event.payload['owner']
    # asset_id = event.payload[]
    # amount = event.payload['amount']
    shares = event.payload['lp_token_minted']
    # price = event.payload['price']

    # # save position
    # position_model = m.OmnipoolPositions(
    #     position_id=position_id,
    #     owner=owner,
    #     asset=asset_id,
    #     amount=amount,
    #     shares=shares,
    #     price=price,
    # )
    # await position_model.save()

    # pair_id = await upsert_pair_model(OMNIPOOL_LP_ASSET_ID, asset_id, 'assethub')

    maker = event.payload['mint_to']
    amount_0 = Decimal(event.payload['amount1_provided'])
    amount_1 = Decimal(event.payload['amount2_provided'])
    # lp_token: int
    # lp_token_minted: int

    # emit join event
    join_event = models.Event(
        event_type='join',
        composite_pk=f'{event.data.block_number}-{event.data.extrinsic_index}-{event.data.index}',
        txn_id=f'{event.data.block_number}-{event.data.extrinsic_index}-{event.data.index}',
        txn_index=event.data.extrinsic_index or event.data.index,
        event_index=event.data.index,
        maker=maker,
        pair_id=pool.id,
        amount_0=amount_0,
        amount_1=amount_1,
        price_native=amount_0 / amount_1,
        # TODO: get and update pool fields
        # reserves_asset_0
        # reserves_asset_1
    )
    await join_event.save()
