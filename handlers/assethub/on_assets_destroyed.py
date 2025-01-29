from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import DoesNotExist

from dex_screener import models as m
from dex_screener.types.assethub.substrate_events.assets_destroyed import AssetsDestroyedPayload


async def on_assets_destroyed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsDestroyedPayload],
) -> None:
    try:
        # FIXME: TypedDict "V601" has no key "asset_id"
        asset = await m.Asset.get(id=event.payload['asset_id'])  # type: ignore
    except DoesNotExist:
        error_str = f'Asset not found: {event.payload['asset_id']}'
        ctx.logger.error(error_str)
        return
    await asset.delete()
    ctx.logger.info('Deleting asset %s', asset.get_repr())
