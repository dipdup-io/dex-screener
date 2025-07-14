from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import DexEvent
from dex_screener.models import Pool
from dex_screener.types.hydradx.substrate_events.stableswap_liquidity_added import StableswapLiquidityAddedPayload
from service.dex.stableswap.stableswap_service import StableSwapService
from service.event.const import DexScreenerEventType


async def on_liquidity_added(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapLiquidityAddedPayload],
) -> None:
    pool_id = StableSwapService.get_pool_id(event.payload['pool_id'])
    pool = await Pool.get(account=pool_id)

    for asset_id in event.payload['assets']:
        pair_id = StableSwapService.get_pair_id(pool, int(asset_id), pool.lp_token_id)

        # pair = await Pair.get(id=pair_id).prefetch_related('asset_0', 'asset_1')
        # TODO: split lp token amount to asset amounts

        await DexEvent.create(
            event_index=event.data.index,
            name=event.data.name,
            block_id=event.data.level,
            tx_index=event.data.extrinsic_index if event.data.extrinsic_index is not None else 0,
            pair_id=pair_id,
            maker=event.payload['who'],
            amount_0='0',  # TODO: extract amount_0 from lp token amount
            amount_1='0',  # TODO: extract amount_1 from asset amount
            event_type=DexScreenerEventType.Join,
        )
