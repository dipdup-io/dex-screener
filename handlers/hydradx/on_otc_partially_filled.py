from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.otc_partially_filled import OTCPartiallyFilledPayload


async def on_otc_partially_filled(
    ctx: HandlerContext,
    event: SubstrateEvent[OTCPartiallyFilledPayload],
) -> None: ...
