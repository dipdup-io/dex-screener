from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.balances_withdraw import BalancesWithdrawPayload


async def on_balances_withdraw(
    ctx: HandlerContext,
    event: SubstrateEvent[BalancesWithdrawPayload],
) -> None: ...
