from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.balances_deposit import BalancesDepositPayload
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent


async def on_balances_deposit(
    ctx: HandlerContext,
    event: SubstrateEvent[BalancesDepositPayload],
) -> None:
    ...