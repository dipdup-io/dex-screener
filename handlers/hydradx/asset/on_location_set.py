from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.handlers.hydradx.asset.asset_location import get_asset_location
from dex_screener.handlers.hydradx.asset.asset_location.types import AssetRegistryLocation
from dex_screener.handlers.hydradx.asset.asset_location.types import NativeLocation
from dex_screener.handlers.hydradx.asset.asset_location.types import Parachain
from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError
from dex_screener.handlers.hydradx.asset.asset_type.hydration_external_asset import HydrationExternalAsset

if TYPE_CHECKING:
    from dipdup.context import HandlerContext
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.models import Asset
    from dex_screener.types.hydradx.substrate_events.asset_registry_location_set import AssetRegistryLocationSetPayload


async def on_location_set(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetRegistryLocationSetPayload],
) -> None:
    try:
        match AssetRegistryLocation.from_event(event_payload=event.payload):  # type: ignore[arg-type]
            case AssetRegistryLocation(
                asset_id=int(asset_id),
                location=NativeLocation(
                    parents=1,
                    interior=(Parachain(parachain_id), *_) as interior_value,
                ),
            ):
                pass

            case _:
                raise InvalidEventDataError(f'Unhandled AssetNativeLocation: {event.payload}.')

        asset_location = get_asset_location(ctx, int(parachain_id))
        asset: Asset = await asset_location.update_asset_with_external_metadata(asset_id, interior_value, event)

        ctx.logger.info('Fetched External Asset Location for asset: %s.', asset)
    except InvalidEventDataError as exception:
        match AssetRegistryLocation.from_event(event_payload=event.payload):  # type: ignore[arg-type]
            case AssetRegistryLocation(
                asset_id=int(asset_id),
            ):
                asset = await HydrationExternalAsset.update_asset(asset_id, {}, event)
                ctx.logger.info('Unknown Location. Saved just asset_id: %s.', asset)
            case _:
                ctx.logger.error('Skipped External Metadata update: %s', exception)
                raise
