from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.xyk_buy_executed import XykBuyExecutedPayload


async def on_buy_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[XykBuyExecutedPayload],
) -> None:
    print(event.payload)
