from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.lbp_pool_updated import LBPPoolUpdatedPayload


async def on_pool_updated(
    ctx: HandlerContext,
    event: SubstrateEvent[LBPPoolUpdatedPayload],
) -> None: ...
