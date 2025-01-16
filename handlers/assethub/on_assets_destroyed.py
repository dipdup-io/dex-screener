from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_destroyed import AssetsDestroyedPayload
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent


async def on_assets_destroyed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsDestroyedPayload],
) -> None:
    asset = await models.Asset.get(id=event.payload['asset_id'])
    await asset.delete()
    ctx.logger.info('Deleting asset `%s` (%s)', asset.name, asset.id)