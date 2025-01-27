from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.omnipool_position_destroyed import OmnipoolPositionDestroyedPayload


async def on_omnipool_position_destroyed(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolPositionDestroyedPayload],
) -> None: ...
