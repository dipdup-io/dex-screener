from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from reserves.handlers.batch import RuntimeFlag
from reserves.models import BalanceHistory
from reserves.models import BalanceUpdateEvent
from reserves.models import SupplyHistory
from reserves.types.hydradx.substrate_events.balances_burned import BalancesBurnedPayload
from reserves.types.hydradx.substrate_events.balances_deposit import BalancesDepositPayload
from reserves.types.hydradx.substrate_events.balances_minted import BalancesMintedPayload
from reserves.types.hydradx.substrate_events.balances_withdraw import BalancesWithdrawPayload

BalancesUpdatePayload = BalancesDepositPayload | BalancesWithdrawPayload | BalancesMintedPayload | BalancesBurnedPayload


async def on_balance_updated(
    ctx: HandlerContext,
    event: SubstrateEvent[BalancesUpdatePayload],
) -> None:
    ctx.logger.debug('%s event: %s-%s.', event.name, event.data.level, event.data.index)

    asset_id = 0
    match event.name:
        case 'Balances.Deposit':
            account = event.payload['who']
            for amount_key in ['deposit', 'amount']:
                if amount_key in event.payload:
                    break
            balance_update = event.payload[amount_key]
        case 'Balances.Minted':
            account = event.payload['who']
            balance_update = event.payload['amount']
        case 'Balances.Withdraw':
            account = event.payload['who']
            for amount_key in ['value', 'amount']:
                if amount_key in event.payload:
                    break
            balance_update = -event.payload[amount_key]
        case 'Balances.Burned':
            account = event.payload['who']
            balance_update = -event.payload['amount']
        case _:
            raise ValueError(event)

    await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

    if RuntimeFlag.synchronized:
        await BalanceHistory.insert(account, asset_id)
        await SupplyHistory.insert(asset_id)
