from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_created import AssetsCreatedPayload


async def on_assets_created(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsCreatedPayload],
) -> None:
    asset = models.Asset(
        id=event.payload['asset_id'],
        name='...',
        symbol='...',
    )
    await asset.save()
    ctx.logger.info('Creating asset %s', asset.get_repr())
