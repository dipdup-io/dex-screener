from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from reserves.models import AccountAssetBalanceCache
from reserves.models import BalanceUpdateEvent
from reserves.types.hydradx.substrate_events.currencies_balance_updated import CurrenciesBalanceUpdatedPayload


async def on_balance_set(
    ctx: HandlerContext,
    event: SubstrateEvent[CurrenciesBalanceUpdatedPayload],
) -> None:
    ctx.logger.debug('%s event: %s-%s.', event.name, event.data.level, event.data.index)

    account = event.payload['who']
    asset_id = event.payload['currency_id']
    latest_balance = await AccountAssetBalanceCache.get_latest_balance(account, asset_id)
    balance = event.payload['amount']
    balance_update = balance - latest_balance

    await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)
