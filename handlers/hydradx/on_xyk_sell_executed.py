from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.xyk_sell_executed import XYKSellExecutedPayload


async def on_xyk_sell_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKSellExecutedPayload],
) -> None: ...
