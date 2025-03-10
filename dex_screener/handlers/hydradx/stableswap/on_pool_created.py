from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.service.dex.stableswap.stableswap_service import StableSwapService
from dex_screener.types.hydradx.substrate_events.stableswap_pool_created import StableswapPoolCreatedPayload


async def on_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapPoolCreatedPayload],
) -> None:
    pool = await StableSwapService.register_pool(event)
    await StableSwapService.register_pair(pool, event)
