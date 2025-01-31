from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.handlers.hydradx.asset.asset_location import get_asset_location
from dex_screener.handlers.hydradx.asset.asset_location.types import AssetRegistryLocation
from dex_screener.types.hydradx.substrate_events.asset_registry_location_set import AssetRegistryLocationSetPayload


async def on_location_set(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetRegistryLocationSetPayload],
) -> None:
    # match AssetRegistryLocation.from_event(payload=event.payload):
    #     case AssetRegistryLocation(
    #         asset_id=int(asset_id),
    #         location=NativeLocation(
    #             parents=1,
    #             interior=[Parachain(parachain_id), *_] as interior_value,
    #         ),
    #     ):
    #         pass

    #     case _:
    #         ctx.logger.error('Unhandled AssetNativeLocation')
    #         return

    location = AssetRegistryLocation.from_event(payload=event.payload)

    try:
        asset_location = get_asset_location(int(location.asset_id))
        asset = await asset_location.update_asset_with_external_metadata(location.asset_id, asset_location[1:], event)

        ctx.logger.info('Fetched External Asset Location for asset: %s', asset)
    except ValueError as e:
        ctx.logger.warning(e)
