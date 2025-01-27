from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.otc_cancelled import OTCCancelledPayload


async def on_otc_cancelled(
    ctx: HandlerContext,
    event: SubstrateEvent[OTCCancelledPayload],
) -> None: ...
