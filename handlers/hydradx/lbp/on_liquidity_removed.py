from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.lbp_liquidity_removed import LBPLiquidityRemovedPayload


async def on_liquidity_removed(
    ctx: HandlerContext,
    event: SubstrateEvent[LBPLiquidityRemovedPayload],
) -> None: ...
