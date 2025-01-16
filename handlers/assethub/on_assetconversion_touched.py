from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.asset_conversion_touched import AssetConversionTouchedPayload


async def on_assetconversion_touched(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionTouchedPayload],
) -> None:
    raise NotImplementedError