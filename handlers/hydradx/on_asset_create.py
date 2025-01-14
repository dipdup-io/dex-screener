from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import Asset
from dex_screener.types.hydradx.substrate_events.asset_registry_registered import AssetRegistryRegisteredPayload


async def on_asset_create(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetRegistryRegisteredPayload],
) -> None:
    if isinstance(event.data.args, list):
        asset_id, asset_name = event.data.args[0], event.data.args[1]
    elif isinstance(event.data.args, dict):
        asset_id, asset_name = event.data.args['assetId'], event.data.args['assetName']
    else:
        ctx.logger.error('Unknown event args format: %s', event.data.args)
        return

    await Asset.create(
        id=asset_id,
        name=asset_name,
        symbol='',
        # total_supply
        # circulating_supply
        # coin_gecko_id
        # coin_market_cap_id
        # metadata
    )
