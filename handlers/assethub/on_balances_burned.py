from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.balances_burned import BalancesBurnedPayload


async def on_balances_burned(
    ctx: HandlerContext,
    event: SubstrateEvent[BalancesBurnedPayload],
) -> None: ...
