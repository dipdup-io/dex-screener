import asyncio
from decimal import Decimal

import httpx
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

import dex_screener
from dex_screener.models import AssetPoolReserve
from dex_screener.models import DexEvent
from dex_screener.models import DexKey
from dex_screener.models import DexScreenerEventType
from dex_screener.models import Pair
from dex_screener.proxy import ReservesReceivingError, get_account_balance
from dex_screener.proxy import get_reserves_by_lp
from dex_screener.types.hydradx.substrate_events.xyk_liquidity_added import XYKLiquidityAddedPayload


async def on_liquidity_added(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKLiquidityAddedPayload],
) -> None:
    # NOTE: Sort assets and amounts
    asset_0, asset_1 = int(event.payload['asset_a']), int(event.payload['asset_b'])
    amount_0, amount_1 = event.payload['amount_a'], event.payload['amount_b']
    if asset_0 > asset_1:
        asset_0, asset_1 = asset_1, asset_0
        amount_0, amount_1 = amount_1, amount_0

    # NOTE: Get pair by key and assets
    pair = (
        await Pair.filter(
            dex_key=DexKey.IsolatedPool,
            asset_0_id=asset_0,
            asset_1_id=asset_1,
        )
        .prefetch_related('asset_0', 'asset_1', 'pool')
        .get()
    )

    # get_account_balance
    async with httpx.AsyncClient() as client:
        dex_screener.proxy._client = client

        tries = 0
        while True:
            try:
                reserves_0 = await get_reserves_by_lp('http://localhost:8081/v1/graphql', asset_0, event.data.level)
                reserves_1 = await get_reserves_by_lp('http://localhost:8081/v1/graphql', asset_1, event.data.level)
                # shares = await get_reserves_by_lp('http://localhost:8081/v1/graphql', pair.pool.lp_token_id, event.data.level)
            except ReservesReceivingError as e:
                tries += 1
                ctx.logger.warning('Attempt #%s failed to get reserves for pair %s: %s. Retrying...', tries, pair.id, e)
                await asyncio.sleep(1)
                continue

    # NOTE: Get reserve models
    # reserves_0_model = await AssetPoolReserve.get(pool=pair.pool, asset=asset_0)
    # reserves_1_model = await AssetPoolReserve.get(pool=pair.pool, asset=asset_1)
    # int(Decimal(reserves_0_model.reserve) * (10**pair.asset_0.decimals))

    # NOTE: XYK: Calculate and update pool shares
    # new_shares = int(int_reserves_0 * amount_0 / (int(pair.pool.shares) or 1))
    # pair.pool.shares = str(int(pair.pool.shares) + new_shares)
    # await pair.pool.save()

    # NOTE: Convert amounts to major units
    # amount_0 = pair.asset_0.from_minor(amount_0)
    # amount_1 = pair.asset_1.from_minor(amount_1)
    reserves_0 = pair.asset_0.amount(reserves_0)
    reserves_1 = pair.asset_1.amount(reserves_1)

    # NOTE: Update reserves
    # reserves_0_model.reserve = str(reserves_0)
    # reserves_1_model.reserve = str(reserves_1)
    # await reserves_0_model.save()
    # await reserves_1_model.save()

    # NOTE: Create DexEvent
    await DexEvent.create(
        event_type=DexScreenerEventType.Join,
        name=event.data.name,
        maker=event.payload['who'],
        pair_id=pair.id,
        amount_0_in=None,
        amount_1_in=None,
        amount_0_out=None,
        amount_1_out=None,
        price=None,
        amount_0=str(amount_0),
        amount_1=str(amount_1),
        asset_0_reserve=reserves_0,
        asset_1_reserve=reserves_1,
        event_index=event.data.index,
        tx_index=event.data.extrinsic_index if event.data.extrinsic_index is not None else 0,
        block_id=event.data.level,
    )

    ctx.logger.debug(
        'Liquidity added to pair %s: %s %s, %s %s.',
        pair.id,
        amount_0,
        pair.asset_0.symbol,
        amount_1,
        pair.asset_1.symbol,
    )
