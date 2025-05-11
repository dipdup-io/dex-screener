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

    for account, balance_update in [
        (event.payload['from'], -event.payload[amount_key]),
        (event.payload['to'], event.payload[amount_key]),
    ]:
        await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

        if RuntimeFlag.synchronized:
            await BalanceHistory.insert(account, asset_id)
