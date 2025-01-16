from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.models.pool import get_pool_id
from dex_screener.types.assethub.substrate_events.asset_conversion_liquidity_added import (
    AssetConversionLiquidityAddedPayload,
)


async def on_assetconversion_liquidity_added(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionLiquidityAddedPayload],
) -> None:
    pool_id = get_pool_id(event.payload['pool_id'])
    pool = await models.Pool.get(id=pool_id)
    ctx.logger.info('Liquidity added to pool `%s`', pool.id)
