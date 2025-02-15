from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import AssetPoolReserve
from dex_screener.models import CachedPools
from dex_screener.models import Pool
from dex_screener.types.hydradx.substrate_events.currencies_balance_updated import CurrenciesBalanceUpdatedPayload


async def on_balance_updated(
    ctx: HandlerContext,
    event: SubstrateEvent[CurrenciesBalanceUpdatedPayload],
) -> None:
    if event.payload['who'] not in CachedPools.account_list:
        return

    pool = await Pool.get(account=event.payload['who'])
    await AssetPoolReserve.update_or_create(
        pool_id=pool.id,
        asset_id=event.payload['currency_id'],
        defaults={
            'reserve': event.payload['amount'],
        },
    )
