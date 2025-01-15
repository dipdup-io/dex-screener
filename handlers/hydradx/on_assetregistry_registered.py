from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import Asset
from dex_screener.types.hydradx.substrate_events.asset_registry_registered import AssetRegistryRegisteredPayload


async def on_asset_create(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetRegistryRegisteredPayload],
) -> None:
    id_ = event.payload['asset_id']
    name = event.payload.get('asset_name') or event.payload.get('name') or id_

    asset = Asset(
        id=id_,
        name=name,
        # NOTE: Available after some block
        symbol=event.payload.get('symbol') or name,
        # total_supply
        # circulating_supply
        # coin_gecko_id
        # coin_market_cap_id
        # metadata
    )

    ctx.logger.info('Creating asset %s', asset.__dict__)
    await asset.save()
