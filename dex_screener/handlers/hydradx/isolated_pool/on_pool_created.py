from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.service.dex.isolated_pool.isolated_pool_service import IsolatedPoolService
from dex_screener.types.hydradx.substrate_events.xyk_pool_created import XYKPoolCreatedPayload


async def on_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKPoolCreatedPayload],
) -> None:
    pool = await IsolatedPoolService.register_pool(event)
    await IsolatedPoolService.register_pair(pool, event)
