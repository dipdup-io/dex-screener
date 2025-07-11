from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.xyk_pool_destroyed import XYKPoolDestroyedPayload


async def on_pool_destroyed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKPoolDestroyedPayload],
) -> None:
    pass
