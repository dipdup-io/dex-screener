from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models
from dex_screener.types.assethub.substrate_events.asset_conversion_liquidity_removed import (
    AssetConversionLiquidityRemovedPayload,
)


async def on_assetconversion_liquidity_removed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionLiquidityRemovedPayload],
) -> None:
    pool_id = models.get_pool_id(event.payload)
    if not pool_id:
        return

    pool = await models.Pool.get(id=pool_id)
    ctx.logger.info('Liquidity added to pool `%s`', pool.id)

    # raise NotImplementedError
