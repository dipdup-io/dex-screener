from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.omnipool_sell_executed import OmnipoolSellExecutedPayload


async def on_omnipool_sell_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolSellExecutedPayload],
) -> None: ...
