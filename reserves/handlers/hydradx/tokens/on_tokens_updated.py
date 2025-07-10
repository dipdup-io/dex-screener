from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from reserves.handlers.batch import RuntimeFlag
from reserves.models import BalanceHistory
from reserves.models import BalanceUpdateEvent
from reserves.models import SupplyHistory
from reserves.types.hydradx.substrate_events.tokens_deposited import TokensDepositedPayload
from reserves.types.hydradx.substrate_events.tokens_withdrawn import TokensWithdrawnPayload

TokensUpdatePayload = TokensDepositedPayload | TokensWithdrawnPayload



async def on_balance_updated(
    ctx: HandlerContext,
    event: SubstrateEvent[TokensUpdatePayload],
) -> None:
    ctx.logger.debug('%s event: %s-%s.', event.name, event.data.level, event.data.index)

    asset_id = event.payload['currency_id']
    account = event.payload['who']
    match event.name:
        case 'Tokens.Deposited':
            balance_update = event.payload['amount']
        case 'Tokens.Withdrawn':
            balance_update = -event.payload['amount']
        case _:
            raise ValueError(event)

    await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

    if RuntimeFlag.realtime:
        await BalanceHistory.insert(account, asset_id)
        await SupplyHistory.insert(asset_id)
