from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from reserves.handlers.batch import RuntimeFlag
from reserves.models import BalanceHistory
from reserves.models import BalanceUpdateEvent
from reserves.types.hydradx.substrate_events.currencies_transferred import CurrenciesTransferredPayload
from reserves.types.hydradx.substrate_events.tokens_transfer import TokensTransferPayload


async def on_balance_transfer(
    ctx: HandlerContext,
    event: SubstrateEvent[CurrenciesTransferredPayload | TokensTransferPayload],
) -> None:
    ctx.logger.debug('%s event: %s-%s.', event.name, event.data.level, event.data.index)

    asset_id = event.payload['currency_id']

    for account, balance_update in [
        (event.payload['from'], -event.payload['amount']),
        (event.payload['to'], event.payload['amount']),
    ]:
        await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

        if RuntimeFlag.synchronized:
            await BalanceHistory.insert(account, asset_id)
