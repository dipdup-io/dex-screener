from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.service.dex.lbp.lbp_service import LBPService
from dex_screener.types.hydradx.substrate_events.lbp_pool_created import LBPPoolCreatedPayload


async def on_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[LBPPoolCreatedPayload],
) -> None:
    pool = await LBPService.register_pool(event)
    await LBPService.register_pair(pool, event)
