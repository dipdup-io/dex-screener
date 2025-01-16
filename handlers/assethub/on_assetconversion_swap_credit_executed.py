from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.asset_conversion_swap_credit_executed import (
    AssetConversionSwapCreditExecutedPayload,
)


async def on_assetconversion_swap_credit_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionSwapCreditExecutedPayload],
) -> None:
    raise NotImplementedError
