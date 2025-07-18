
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import DexEvent
from dex_screener.models import DexKey
from dex_screener.models import DexScreenerEventType
from dex_screener.models import Pair
from dex_screener.types.hydradx.substrate_events.xyk_liquidity_added import XYKLiquidityAddedPayload
from utils import get_balance_by_account
from utils import wait_for_reserves


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

    await wait_for_reserves(event.data.level)
    reserves_0 = await get_balance_by_account(
        account=pair.pool.account,
        asset_id=asset_0,
        level=event.data.level,
    )
    reserves_1 = await get_balance_by_account(
        account=pair.pool.account,
        asset_id=asset_1,
        level=event.data.level,
    )

    amount_0 = str(pair.asset_0.from_minor(amount_0))
    amount_1 = str(pair.asset_1.from_minor(amount_1))
    asset_0_reserve = str(pair.asset_0.from_minor(reserves_0))
    asset_1_reserve = str(pair.asset_1.from_minor(reserves_1))

    # NOTE: Create DexEvent
    await DexEvent.create(
        event_type=DexScreenerEventType.Join,
        name=event.data.name,
        maker=event.payload['who'],
        pair_id=pair.id,
        amount_0=amount_0,
        amount_1=amount_1,
        asset_0_reserve=asset_0_reserve,
        asset_1_reserve=asset_1_reserve,
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
