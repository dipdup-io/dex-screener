from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from scalecodec import ss58_decode  # type: ignore[import-untyped]
from tortoise.functions import Sum

from reserves import models as models
from reserves.handlers.batch import RuntimeFlag
from reserves.models import BalanceHistory
from reserves.models import BalanceUpdateEvent
from reserves.models import SupplyHistory
from reserves.types.hydradx.substrate_events.currencies_balance_updated import CurrenciesBalanceUpdatedPayload


async def on_currencies_balance_updated(
    ctx: HandlerContext,
    event: SubstrateEvent[CurrenciesBalanceUpdatedPayload],
) -> None:
    account = event.payload['who']
    asset_id = event.payload['currency_id']
    balance = event.payload['amount']

    if not account.startswith('0x'):
        account = f'0x{ss58_decode(account)}'

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

    balance_update = balance - latest_balance

    await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

    if RuntimeFlag.realtime:
        await BalanceHistory.insert(account, asset_id)
        await SupplyHistory.insert(asset_id)
