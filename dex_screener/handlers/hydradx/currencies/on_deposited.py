from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import AssetPoolReserve
from dex_screener.models import CachedPools
from dex_screener.models import Pool
from dex_screener.types.hydradx.substrate_events.currencies_deposited import CurrenciesDepositedPayload


async def on_deposited(
    ctx: HandlerContext,
    event: SubstrateEvent[CurrenciesDepositedPayload],
) -> None:
    if event.payload['who'] not in CachedPools.account_list:
        return

    pool = await Pool.get(account=event.payload['who'])
    record, _ = await AssetPoolReserve.get_or_create(
        pool_id=pool.account,
        asset_id=event.payload['currency_id'],
        defaults={
            'reserve': 0,
        },
    )
    if record.reserve is None:
        record.reserve = 0
    record.reserve = int(record.reserve) + int(event.payload['amount'])
    await record.save()
