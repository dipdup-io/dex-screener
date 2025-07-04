from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.service.dex.omnipool.omnipool_service import OmnipoolService
from dex_screener.types.hydradx.substrate_events.omnipool_token_added import OmnipoolTokenAddedPayload


async def on_token_added(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolTokenAddedPayload],
) -> None:
    # could be moved to PositionCreated event handler
    pool = await OmnipoolService.get_pool()
    await OmnipoolService.register_pair(pool, event)
