from decimal import Decimal

from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.models import AssetPoolReserve
from dex_screener.models import DexEvent
from dex_screener.models import DexKey
from dex_screener.models import DexScreenerEventType
from dex_screener.models import Pair
from dex_screener.types.hydradx.substrate_events.xyk_liquidity_removed import XYKLiquidityRemovedPayload


async def on_liquidity_removed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKLiquidityRemovedPayload],
) -> None:
    # FIXME: De-camelcasing fails when parsing payload
    if 'assetA' in event.payload:
        event.payload['asset_a'] = event.payload.pop('assetA')  # type: ignore[typeddict-item]
    if 'assetB' in event.payload:
        event.payload['asset_b'] = event.payload.pop('assetB')  # type: ignore[typeddict-item]

    # NOTE: Sort assets
    asset_0, asset_1 = int(event.payload['asset_a']), int(event.payload['asset_b'])
    if asset_0 > asset_1:
        asset_0, asset_1 = asset_1, asset_0

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

    # NOTE: Get reserve models
    reserves_0_model = await AssetPoolReserve.get(pool=pair.pool, asset=asset_0)
    reserves_1_model = await AssetPoolReserve.get(pool=pair.pool, asset=asset_1)
    int_reserves_0 = int(Decimal(reserves_0_model.reserve) * (10**pair.asset_0.decimals))
    int_reserves_1 = int(Decimal(reserves_1_model.reserve) * (10**pair.asset_1.decimals))

    # NOTE: XYK: Calculate amounts from burned shares
    burned_shares = int(event.payload['shares'])
    amount_0 = burned_shares * int_reserves_0 / int(pair.pool.shares)
    amount_1 = burned_shares * int_reserves_1 / int(pair.pool.shares)
    pair.pool.shares = str(int(pair.pool.shares) - burned_shares)
    await pair.pool.save()

    # NOTE: Convert amounts to major units
    amount_0 = pair.asset_0.from_minor(amount_0)
    amount_1 = pair.asset_1.from_minor(amount_1)
    reserves_0 = pair.asset_0.amount(reserves_0_model.reserve)
    reserves_1 = pair.asset_1.amount(reserves_1_model.reserve)

    # NOTE: Update reserves
    reserves_0_model.reserve = str(reserves_0 - amount_0)
    reserves_1_model.reserve = str(reserves_1 - amount_1)
    await reserves_0_model.save()
    await reserves_1_model.save()

    # NOTE: Create DexEvent
    await DexEvent(
        event_type=DexScreenerEventType.Exit,
        name=event.data.name,
        maker=event.payload['who'],
        pair=pair,
        amount_0_in=None,
        amount_1_in=None,
        amount_0_out=str(amount_0),
        amount_1_out=str(amount_1),
        price=None,
        amount_0=str(amount_0),
        amount_1=str(amount_1),
        asset_0_reserve=str(reserves_0),
        asset_1_reserve=str(reserves_1),
        event_index=event.data.index,
        tx_index=event.data.extrinsic_index if event.data.extrinsic_index is not None else 0,
        block_id=event.data.level,
    ).save()

    ctx.logger.debug(
        'Liquidity removed from pair %s: %s %s, %s %s.',
        pair.id,
        amount_0,
        pair.asset_0.symbol,
        amount_1,
        pair.asset_1.symbol,
    )
