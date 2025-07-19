from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import DexEvent
from dex_screener.models import DexScreenerEventType
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.service.dex.stableswap.stableswap_service import get_pair_id
from dex_screener.service.dex.stableswap.stableswap_service import get_pool_account
from dex_screener.types.hydradx.substrate_events.stableswap_liquidity_removed import StableswapLiquidityRemovedPayload
from utils import get_balance_by_account
from utils import wait_for_reserves


async def on_liquidity_removed(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapLiquidityRemovedPayload],
) -> None:
    pool = await Pool.get(lp_token_id=event.payload['pool_id'])

    await wait_for_reserves(event.data.level)

    # NOTE: The amounts field contains asset_id -> amount mappings
    for amount_data in event.payload['amounts']:
        asset_id, amount = int(amount_data['assetId']), int(amount_data['amount'])

        pair_id = get_pair_id(pool, asset_id, pool.lp_token_id)

        pair = await Pair.get(id=pair_id).prefetch_related('asset_0', 'asset_1', 'pool')

        # NOTE: Get current reserves after the event
        reserves_0 = await get_balance_by_account(pair.pool.account, pair.asset_0.id, event.data.level)
        reserves_1 = await get_balance_by_account(pair.pool.account, pair.asset_1.id, event.data.level)

        # NOTE: Determine which asset was removed and calculate amounts
        if asset_id == pair.asset_0.id:
            amount_0, amount_1 = amount, 0
        elif asset_id == pair.asset_1.id:
            amount_0, amount_1 = 0, amount
        else:
            raise Exception

        await DexEvent.create(
            event_type=DexScreenerEventType.Exit,
            name=event.data.name,
            maker=event.payload['who'],
            pair_id=pair_id,
            amount_0=str(pair.asset_0.from_minor(amount_0)),
            amount_1=str(pair.asset_1.from_minor(amount_1)),
            asset_0_reserve=str(pair.asset_0.from_minor(reserves_0)),
            asset_1_reserve=str(pair.asset_1.from_minor(reserves_1)),
            event_index=event.data.index,
            tx_index=event.data.extrinsic_index if event.data.extrinsic_index is not None else 0,
            block_id=event.data.level,
        )

        ctx.logger.debug(
            'Liquidity removed from pair %s: %s %s, %s %s.',
            pair.id,
            pair.asset_0.from_minor(amount_0),
            pair.asset_0.symbol,
            pair.asset_1.from_minor(amount_1),
            pair.asset_1.symbol,
        )
