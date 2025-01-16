from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.asset_conversion_liquidity_removed import (
    AssetConversionLiquidityRemovedPayload,
)


async def on_assetconversion_liquidity_removed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionLiquidityRemovedPayload],
) -> None:
    raise NotImplementedError
