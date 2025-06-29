from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from reserves.handlers.batch import RuntimeFlag
from reserves.models import BalanceHistory
from reserves.models import BalanceUpdateEvent
from reserves.models import SupplyHistory
from reserves.types.hydradx.substrate_events.currencies_balance_updated import CurrenciesBalanceUpdatedPayload
from reserves.types.hydradx.substrate_events.currencies_deposited import CurrenciesDepositedPayload
from reserves.types.hydradx.substrate_events.currencies_withdrawn import CurrenciesWithdrawnPayload

CurrenciesUpdatePayload = CurrenciesDepositedPayload | CurrenciesWithdrawnPayload | CurrenciesBalanceUpdatedPayload


async def on_balance_updated(
    ctx: HandlerContext,
    event: SubstrateEvent[CurrenciesUpdatePayload],
) -> None:
    ctx.logger.debug('%s event: %s-%s.', event.name, event.data.level, event.data.index)

    asset_id = event.payload['currency_id']
    match event.name:
        case 'Currencies.Deposited' | 'Tokens.Deposited':
            account = event.payload['who']
            balance_update = event.payload['amount']
        case 'Currencies.Withdrawn' | 'Tokens.Withdrawn':
            account = event.payload['who']
            balance_update = -event.payload['amount']
        case 'Currencies.BalanceUpdated':
            pass
        case _:
            raise ValueError(event)

    await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

    if RuntimeFlag.realtime:
        await BalanceHistory.insert(account, asset_id)
        await SupplyHistory.insert(asset_id)
