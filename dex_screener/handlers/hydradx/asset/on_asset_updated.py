from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from scalecodec.exceptions import RemainingScaleBytesNotEmptyException
from tortoise.exceptions import IntegrityError

from dex_screener.handlers.hydradx.asset.asset_type import AbstractHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.const import REQUIRED_ASSET_TYPE_MAP
from dex_screener.handlers.hydradx.asset.asset_type.const import UNUSED_ASSET_TYPE_LIST
from dex_screener.types.hydradx.substrate_events.asset_registry_updated import AssetRegistryUpdatedPayload


def get_asset_type(
    event: SubstrateEvent[AssetRegistryUpdatedPayload],
) -> type[AbstractHydrationAsset]:
    try:
        match event.payload:
            case {'asset_type': {'__kind': str(asset_type)}}:
                pass
            case {'type': {'__kind': str(asset_type)}}:
                pass
            case _:
                raise ValueError('Unhandled Event Payload.')

    except (ValueError, RemainingScaleBytesNotEmptyException):
        match event.data.args:
            case {'assetType': {'__kind': str(asset_type)}}:
                pass
            case _:
                raise ValueError('Unhandled Event Data.') from None

    if asset_type in UNUSED_ASSET_TYPE_LIST:
        raise NotImplementedError(f'Unsupported Asset Type: {asset_type}')

    if asset_type in REQUIRED_ASSET_TYPE_MAP:
        return REQUIRED_ASSET_TYPE_MAP[asset_type]

    raise ValueError(f'Unhandled AssetType: `{asset_type}`.')


async def on_asset_updated(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetRegistryUpdatedPayload],
) -> None:
    try:
        asset_type = get_asset_type(event)
    except NotImplementedError:
        return
    except ValueError as exception:
        ctx.logger.warning(exception.args[0])
        return

    try:
        asset = await asset_type.handle_update_asset(event)
        ctx.logger.info('Asset updated: %s.', asset)
    except IntegrityError as exception:
        ctx.logger.error('Asset Update Error: %s', exception.args[0].detail)
        return
