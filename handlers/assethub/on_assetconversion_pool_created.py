from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.models import get_pool_id
from dex_screener.types.assethub.substrate_events.asset_conversion_pool_created import AssetConversionPoolCreatedPayload


async def on_assetconversion_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionPoolCreatedPayload],
) -> None:
    pool_id = get_pool_id(event.payload)
    if not pool_id:
        return

    pool = models.Pool(
        id=pool_id,
        who=event.payload['creator'],
        asset_a=-1,
        asset_b=int(pool_id.split('_')[1]),
        initial_shares_amount=0,
        share_token=event.payload['lp_token'],
    )
    await pool.save()
    ctx.logger.info('Creating pool `%s`', pool.id)
