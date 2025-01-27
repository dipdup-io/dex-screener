from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.omnipool_position_updated import OmnipoolPositionUpdatedPayload


async def on_omnipool_position_updated(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolPositionUpdatedPayload],
) -> None: ...
