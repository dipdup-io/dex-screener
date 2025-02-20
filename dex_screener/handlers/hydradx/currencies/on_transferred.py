from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import AssetPoolReserve
from dex_screener.models import CachedPools
from dex_screener.models import Pool
from dex_screener.types.hydradx.substrate_events.currencies_transferred import CurrenciesTransferredPayload


async def on_transferred(
    ctx: HandlerContext,
    event: SubstrateEvent[CurrenciesTransferredPayload],
) -> None:
    if event.payload['from'] not in CachedPools.account_list and event.payload['to'] not in CachedPools.account_list:
        return

    if event.payload['from'] in CachedPools.account_list:
        record = await AssetPoolReserve.get(
            pool__account=event.payload['from'],
            asset_id=event.payload['currency_id'],
        )
        record.reserve = int(record.reserve) - int(event.payload['amount'])
        await record.save()

    if event.payload['to'] in CachedPools.account_list:
        pool = await Pool.get(account=event.payload['to'])
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
