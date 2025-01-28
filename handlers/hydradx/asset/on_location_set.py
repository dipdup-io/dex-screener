from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.handlers.hydradx.asset.asset_location import get_asset_location
from dex_screener.types.hydradx.substrate_events.asset_registry_location_set import AssetRegistryLocationSetPayload


async def on_location_set(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetRegistryLocationSetPayload],
) -> None:
    match event.payload:
        case {
            'asset_id': int(asset_id),
            'location': {
                'parents': 1,
                'interior': {
                    'value': [{'__kind': 'Parachain', 'value': int(parachain_id)}, *_] as interior_value,
                },
            },
        }:
            pass

        case _:
            ctx.logger.error('Unhandled AssetNativeLocation')
            return

    try:
        asset_location = get_asset_location(parachain_id)
        asset = await asset_location.update_asset_with_external_metadata(asset_id, interior_value, event)

        ctx.logger.info('Fetched External Asset Location for asset: %s', asset)
    except ValueError:
        return
