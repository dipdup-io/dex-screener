from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from reserves.handlers.batch import RuntimeFlag
from reserves.handlers.hydradx.balances.on_balance_set import Sum
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
            account = event.payload['who']
            balance = event.payload['amount']
            latest_balance: int = (
                await BalanceUpdateEvent.filter(  # type: ignore[assignment]
                    asset_id=asset_id,
                    account=account,
                )
                .group_by(
                    'account',
                    'asset_id',
                )
                .annotate(latest_balance=Sum('balance_update'))
                .first()
                .values_list('latest_balance', flat=True)
            )
            if latest_balance is None:
                latest_balance = 0
            balance_update = latest_balance - balance
        case _:
            raise ValueError(event)

    await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

    if RuntimeFlag.realtime:
        await BalanceHistory.insert(account, asset_id)
        await SupplyHistory.insert(asset_id)
