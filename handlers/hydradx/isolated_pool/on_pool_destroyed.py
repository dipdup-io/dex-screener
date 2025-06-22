from dipdup.context import HandlerContext
from dipdup.models import Meta
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.xyk_pool_destroyed import XYKPoolDestroyedPayload


async def on_pool_destroyed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKPoolDestroyedPayload],
) -> None:
    destroyed_pools, _ = await Meta.get_or_create(
        key='destroyed_pools',
        defaults={'value': []},
    )
    destroyed_pools.value.append(event.payload['pool'])
    await destroyed_pools.save()
    ctx.logger.info('Pool destroyed: %s.', event.payload['pool'])
