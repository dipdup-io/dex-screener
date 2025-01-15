from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.otc_filled import OtcFilledPayload


async def on_execute(
    ctx: HandlerContext,
    event: SubstrateEvent[OtcFilledPayload],
) -> None:
    print(event.payload)
