from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import AssetPoolReserve
from dex_screener.models import CachedPools
from dex_screener.types.hydradx.substrate_events.currencies_withdrawn import CurrenciesWithdrawnPayload


async def on_withdrawn(
    ctx: HandlerContext,
    event: SubstrateEvent[CurrenciesWithdrawnPayload],
) -> None:
    if event.payload['who'] not in CachedPools.account_list:
        return

    record = await AssetPoolReserve.get(
        pool__account=event.payload['who'],
        asset_id=event.payload['currency_id'],
    )
    record.reserve = int(record.reserve) - int(event.payload['amount'])
    await record.save()
