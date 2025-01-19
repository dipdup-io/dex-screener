from typing import Any
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.asset_conversion_swap_executed import (
    AssetConversionSwapExecutedPayload,
)


async def on_assetconversion_swap_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionSwapExecutedPayload],
) -> None:
    event.payload.path = models.fix_multilocation(event.payload.path)
    ctx.logger.warning('SwapExecuted: %s', event.payload)
    raise NotImplementedError
