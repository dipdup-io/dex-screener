from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.stableswap_sell_executed import StableswapSellExecutedPayload


async def on_stableswap_sell_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapSellExecutedPayload],
) -> None: ...
