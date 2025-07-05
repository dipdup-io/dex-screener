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
    account = event.payload['who']
    match event.name:
        case 'Currencies.Deposited' | 'Tokens.Deposited':
            balance_update = event.payload['amount']
        case 'Currencies.Withdrawn' | 'Tokens.Withdrawn':
            balance_update = -event.payload['amount']
        case 'Currencies.BalanceUpdated':
            balance_obj = (
                await BalanceHistory.filter(
                    asset_id=asset_id,
                    account=account,
                )
                .order_by('-id')
                .first()
            )
            balance = 0 if balance_obj is None else balance_obj.balance
            balance_update = event.payload['amount'] - balance

        case _:
            raise ValueError(event)

    await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

    if RuntimeFlag.realtime:
        await BalanceHistory.insert(account, asset_id)
        await SupplyHistory.insert(asset_id)
