from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.otc_placed import OtcPlacedPayload


async def on_placing(
    ctx: HandlerContext,
    event: SubstrateEvent[OtcPlacedPayload],
) -> None: ...
