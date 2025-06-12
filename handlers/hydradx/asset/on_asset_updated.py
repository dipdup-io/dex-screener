from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import IntegrityError

from dex_screener.handlers.hydradx.asset.asset_type.abstract_hydration_asset import AbstractHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.const import ASSET_TYPE_MAP
from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError
from dex_screener.types.hydradx.substrate_events.asset_registry_updated import AssetRegistryUpdatedPayload


def get_asset_type(
    event: SubstrateEvent[AssetRegistryUpdatedPayload],
) -> type[AbstractHydrationAsset]:
    match event.payload:
        case {'asset_type': str(asset_type)}:
            pass
        case {'type': str(asset_type)}:
            pass
        case _:
            raise InvalidEventDataError(f'Unhandled Event Payload: {event.payload}.')

    if asset_type in ASSET_TYPE_MAP:
        return ASSET_TYPE_MAP[asset_type]

    raise InvalidEventDataError(f'Unhandled AssetType: `{asset_type}`.')


async def on_asset_updated(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetRegistryUpdatedPayload],
) -> None:
    try:
        asset_type = get_asset_type(event)
    except InvalidEventDataError as exception:
        ctx.logger.error(exception)
        raise

    try:
        asset = await asset_type.handle_update_asset(event)
        ctx.logger.info('Asset updated: %s.', asset)
    except IntegrityError as exception:
        ctx.logger.error('Asset Update Error: %s', exception.args[0].detail)
        raise
