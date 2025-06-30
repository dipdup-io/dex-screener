from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from reserves import models as models
from reserves.types.hydradx.substrate_events.sudo_sudid import SudoSudidPayload


async def on_sudo_sudid(
    ctx: HandlerContext,
    event: SubstrateEvent[SudoSudidPayload],
) -> None: ...
