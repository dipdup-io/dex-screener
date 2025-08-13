from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.models import DexEvent
from dex_screener.models import DexKey
from dex_screener.models import DexScreenerEventType
from dex_screener.models import Pair
from dex_screener.types.hydradx.substrate_events.xyk_liquidity_removed import XYKLiquidityRemovedPayload
from dex_screener.utils import get_asset_supply
from dex_screener.utils import get_reserves_by_pair


async def on_liquidity_removed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKLiquidityRemovedPayload],
) -> None:
    # FIXME: De-camelcasing fails when parsing payload. Probably `snake_to_pascal`
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

    reserves_0, reserves_1 = await get_reserves_by_pair(pair, event.data.level)
    pool_shares = await get_asset_supply(pair.pool.lp_token_id, event.data.level)

    # NOTE: Pool was destroyed after the last liquidity removal, using last known reserves
    # FIXME: Fetch correct amounts from block transfers
    if pool_shares == 0:
        reserves_0, reserves_1 = await get_reserves_by_pair(pair, event.data.level - 1)
        pool_shares = await get_asset_supply(pair.pool.lp_token_id, event.data.level - 1)

    # NOTE: Calculate amounts from burned shares
    burned_shares = int(event.payload['shares'])
    amount_0 = burned_shares * reserves_0 // pool_shares
    amount_1 = burned_shares * reserves_1 // pool_shares

    await DexEvent(
        event_type=DexScreenerEventType.Exit,
        name=event.data.name,
        maker=event.payload['who'],
        pair=pair,
        # NOTE: Convert amounts to major units
        amount_0=pair.asset_0_amount(amount_0),
        amount_1=pair.asset_1_amount(amount_1),
        asset_0_reserve=pair.asset_0_amount(reserves_0),
        asset_1_reserve=pair.asset_1_amount(reserves_1),
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
