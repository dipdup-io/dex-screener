from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.otc_placed import OTCPlacedPayload


async def on_otc_placed(
    ctx: HandlerContext,
    event: SubstrateEvent[OTCPlacedPayload],
) -> None: ...
