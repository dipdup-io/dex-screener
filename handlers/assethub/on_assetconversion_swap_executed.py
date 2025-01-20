from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.handlers.assethub.on_assetconversion_swap_credit_executed import (
    on_assetconversion_swap_credit_executed,
)
from dex_screener.types.assethub.substrate_events.asset_conversion_swap_executed import (
    AssetConversionSwapExecutedPayload,
)


async def on_assetconversion_swap_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionSwapExecutedPayload],
) -> None:
    await on_assetconversion_swap_credit_executed(ctx, event)
