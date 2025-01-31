from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.stableswap_liquidity_removed import StableswapLiquidityRemovedPayload


async def on_liquidity_removed(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapLiquidityRemovedPayload],
) -> None: ...
