from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.asset_conversion_pool_created import AssetConversionPoolCreatedPayload


async def on_assetconversion_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionPoolCreatedPayload],
) -> None: ...
