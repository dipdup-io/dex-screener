from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.xyk_sell_executed import XykSellExecutedPayload
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent


async def on_sell_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[XykSellExecutedPayload],
) -> None:
    ...