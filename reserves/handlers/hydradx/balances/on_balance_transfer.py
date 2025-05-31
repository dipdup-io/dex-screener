from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from reserves.handlers.batch import RuntimeFlag
from reserves.models import BalanceHistory
from reserves.models import BalanceUpdateEvent
from reserves.types.hydradx.substrate_events.balances_transfer import BalancesTransferPayload


async def on_balance_transfer(
    ctx: HandlerContext,
    event: SubstrateEvent[BalancesTransferPayload],
) -> None:
    ctx.logger.debug('%s event: %s-%s.', event.name, event.data.level, event.data.index)

    asset_id = 0

    for amount_key in ['value', 'amount']:
        if amount_key in event.payload:
            break

    if event.payload[amount_key] == 0:  # type: ignore[literal-required]
        return

    for account, balance_update in [
        (event.payload['from'], -event.payload[amount_key]),  # type: ignore[literal-required]
        (event.payload['to'], event.payload[amount_key]),  # type: ignore[literal-required]
    ]:
        await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

        if RuntimeFlag.realtime:
            await BalanceHistory.insert(account, asset_id)
