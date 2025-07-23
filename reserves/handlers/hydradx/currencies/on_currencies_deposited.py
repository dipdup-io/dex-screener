from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from scalecodec import ss58_decode  # type: ignore[import-untyped]

from reserves import models as models
from reserves.handlers.batch import RuntimeFlag
from reserves.models import BalanceHistory
from reserves.models import BalanceUpdateEvent
from reserves.models import SupplyHistory
from reserves.types.hydradx.substrate_events.currencies_deposited import CurrenciesDepositedPayload


async def on_currencies_deposited(
    ctx: HandlerContext,
    event: SubstrateEvent[CurrenciesDepositedPayload],
) -> None:
    account = event.payload['who']
    asset_id = event.payload['currency_id']
    balance_update = event.payload['amount']

    if not account.startswith('0x'):
        account = f'0x{ss58_decode(account)}'

    await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

    if RuntimeFlag.realtime:
        await BalanceHistory.insert(account, asset_id)
        await SupplyHistory.insert(asset_id)
