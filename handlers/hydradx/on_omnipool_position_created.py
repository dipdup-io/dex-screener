from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.omnipool_position_created import OmnipoolPositionCreatedPayload


async def on_omnipool_position_created(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolPositionCreatedPayload],
) -> None: ...
