from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.stableswap_liquidity_added import StableswapLiquidityAddedPayload


async def on_liquidity_added(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapLiquidityAddedPayload],
) -> None: ...
