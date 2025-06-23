from dipdup.context import HandlerContext
from dipdup.models import Meta
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import IntegrityError

from dex_screener.service.dex.isolated_pool.isolated_pool_service import IsolatedPoolService
from dex_screener.types.hydradx.substrate_events.xyk_pool_created import XYKPoolCreatedPayload


async def on_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKPoolCreatedPayload],
) -> None:
    try:
        pool = await IsolatedPoolService.register_pool(event)
        await IsolatedPoolService.register_pair(pool, event)
    except IntegrityError:
        destroyed_pools = await Meta.get(key='destroyed_pools')
        if event.payload['pool'] not in destroyed_pools.value:
            raise
        ctx.logger.info('Pool %s was previously destroyed, skipping registration.', event.payload['pool'])
