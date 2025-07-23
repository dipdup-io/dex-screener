from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from scalecodec import ss58_decode  # type: ignore[import-untyped]

from reserves.handlers.batch import RuntimeFlag
from reserves.models import BalanceHistory
from reserves.models import BalanceUpdateEvent
from reserves.types.hydradx.substrate_events.currencies_transferred import CurrenciesTransferredPayload


async def on_currencies_transferred(
    ctx: HandlerContext,
    event: SubstrateEvent[CurrenciesTransferredPayload],
) -> None:
    asset_id = event.payload['currency_id']
    amount = event.payload['amount']
    from_account = event.payload['from']
    to_account = event.payload['to']
    if not from_account.startswith('0x'):
        from_account = f'0x{ss58_decode(from_account)}'
    if not to_account.startswith('0x'):
        to_account = f'0x{ss58_decode(to_account)}'

    if amount == 0:
        return

    for account, balance_update in [
        (from_account, -amount),  # type: ignore[literal-required]
        (to_account, amount),  # type: ignore[literal-required]
    ]:
        await BalanceUpdateEvent.insert(event, account, asset_id, balance_update)

        if RuntimeFlag.realtime:
            await BalanceHistory.insert(account, asset_id)
