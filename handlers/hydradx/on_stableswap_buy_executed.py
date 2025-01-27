from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.stableswap_buy_executed import StableswapBuyExecutedPayload


async def on_stableswap_buy_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapBuyExecutedPayload],
) -> None: ...
