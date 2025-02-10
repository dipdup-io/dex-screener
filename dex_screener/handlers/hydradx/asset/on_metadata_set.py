from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import IntegrityError

from dex_screener.handlers.hydradx.asset.asset_type.hydration_token_asset import HydrationTokenAsset
from dex_screener.types.hydradx.substrate_events.asset_registry_metadata_set import AssetRegistryMetadataSetPayload


async def on_metadata_set(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetRegistryMetadataSetPayload],
) -> None:
    try:
        asset = await HydrationTokenAsset.handle_update_asset(event)
        ctx.logger.info('Asset Metadata updated: %s.', asset)
    except IntegrityError as exception:
        ctx.logger.error('Asset Metadata Update Error: %s', exception.args[0].detail)
        raise
