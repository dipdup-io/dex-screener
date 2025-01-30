from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as m
from dex_screener.types.assethub.substrate_events.assets_created import AssetsCreatedPayload


async def on_assets_created(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsCreatedPayload],
) -> None:
    # NOTE: Already created in `on_restart` hook
    if event.payload['asset_id'] == 0:
        return

    asset = m.Asset(
        id=event.payload['asset_id'],
        name='...',
        symbol='...',
    )
    await asset.save()
    ctx.logger.info('Creating asset %s', repr(asset))
