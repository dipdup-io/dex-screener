from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import DoesNotExist

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_metadata_cleared import AssetsMetadataClearedPayload


async def on_assets_metadata_cleared(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsMetadataClearedPayload],
) -> None:
    try:
        asset = await models.Asset.filter(id=event.payload['asset_id']).get()
    except DoesNotExist:
        error_str = f'Asset not found: {event.payload['asset_id']}'
        ctx.logger.error(error_str)
        return
    asset.name = '...'
    asset.symbol = '...'
    asset.metadata = {}
    await asset.save()
    ctx.logger.info('Clearing asset metadata %s', asset.get_repr())
