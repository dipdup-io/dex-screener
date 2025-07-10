from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.handlers.hydradx import liquidity_added
from dex_screener.types.hydradx.substrate_events.lbp_liquidity_added import LBPLiquidityAddedPayload


async def on_liquidity_added(
    ctx: HandlerContext,
    event: SubstrateEvent[LBPLiquidityAddedPayload],
) -> None:
    await liquidity_added(ctx, event)
