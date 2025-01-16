from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_metadata_set import AssetsMetadataSetPayload


async def on_assets_metadata_set(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsMetadataSetPayload],
) -> None:
    asset = await models.Asset.filter(id=event.payload['asset_id']).get()
    asset.name = event.payload['name']
    asset.symbol = event.payload['symbol']
    asset.metadata = {
        'decimals': event.payload['decimals'],
        'is_frozen': event.payload['is_frozen'],
    }
    await asset.save()
    ctx.logger.info('Updating asset metadata `%s` (%s)', asset.name, asset.id)
