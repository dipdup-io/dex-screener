from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.balances_transfer import BalancesTransferPayload


async def on_transfer(
    ctx: HandlerContext,
    event: SubstrateEvent[BalancesTransferPayload],
) -> None: ...
