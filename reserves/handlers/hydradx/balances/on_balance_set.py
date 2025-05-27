from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from scalecodec import ss58_decode  # type: ignore[import-untyped]
from tortoise.functions import Sum

from reserves.handlers.batch import RuntimeFlag
from reserves.models import BalanceHistory
from reserves.models import BalanceUpdateEvent
from reserves.models import SupplyHistory
from reserves.types.hydradx.substrate_events.balances_balance_set import BalancesBalanceSetPayload


async def on_balance_set(
    ctx: HandlerContext,
    event: SubstrateEvent[BalancesBalanceSetPayload],
) -> None:
    ctx.logger.debug('%s event: %s-%s.', event.name, event.data.level, event.data.index)

    account = event.payload['who']
    if not account.startswith('0x'):
        account = f'0x{ss58_decode(account)}'
    asset_id = 0

    latest_balance: int = (
        await BalanceUpdateEvent.filter(
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

    balance = event.payload['free'] + event.payload['reserved']
    balance_update = balance - latest_balance

    await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

    if RuntimeFlag.realtime:
        await BalanceHistory.insert(account, asset_id)
        await SupplyHistory.insert(asset_id)
