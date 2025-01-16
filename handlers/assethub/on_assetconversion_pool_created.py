from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.models.pool import get_pool_id
from dex_screener.types.assethub.substrate_events.asset_conversion_pool_created import AssetConversionPoolCreatedPayload


async def on_assetconversion_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionPoolCreatedPayload],
) -> None:
    pool = models.Pool(
        id=get_pool_id(event.payload['pool_id']),
        who=event.payload['creator'],
        asset_a=0,
        asset_b=0,
        initial_shares_amount=0,
        share_token=0,
    )
    await pool.save()
    ctx.logger.info('Creating pool `%s`', pool.id)
