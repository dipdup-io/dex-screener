from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.service.dex.isolated_pool.isolated_pool_service import destroyed_pools
from dex_screener.types.hydradx.substrate_events.xyk_pool_destroyed import XYKPoolDestroyedPayload


async def on_pool_destroyed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKPoolDestroyedPayload],
) -> None:
    destroyed_pools.add(event.payload['pool'])
