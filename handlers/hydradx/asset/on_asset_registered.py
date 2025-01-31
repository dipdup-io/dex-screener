from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.handlers.hydradx.asset.asset_type import AbstractHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type import InvalidEventDataError
from dex_screener.handlers.hydradx.asset.asset_type.const import ASSET_TYPE_MAP
from dex_screener.types.hydradx.substrate_events.asset_registry_registered import AssetRegistryRegisteredPayload


def get_asset_type(
    event: SubstrateEvent[AssetRegistryRegisteredPayload],
) -> type[AbstractHydrationAsset]:
    # try:

    if 'asset_type' in event.payload:
        asset_type = event.payload['asset_type']
    elif 'type' in event.payload:
        asset_type = event.payload['type']
    else:
        raise InvalidEventDataError('Unhandled Event Payload.')

    # except (AssertionError, RemainingScaleBytesNotEmptyException, ValueError, NotImplementedError):
    #     if '__kind' in event.data.args.get('assetType', {}):
    #         asset_type = event.data.args['assetType']
    #     else:
    #         raise InvalidEventDataError('Unhandled Event Data.') from None

    if asset_type in ASSET_TYPE_MAP:
        return ASSET_TYPE_MAP[asset_type]

    raise InvalidEventDataError(f'Unhandled AssetType: `{asset_type}`.')


async def on_asset_registered(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetRegistryRegisteredPayload],
) -> None:
    try:
        asset_type = get_asset_type(event)
    except InvalidEventDataError as exception:
        ctx.logger.warning(exception.args[0])
        return

    asset = await asset_type.handle_register_asset(event)
    ctx.logger.info('Asset registered: %s.', asset.get_repr())
