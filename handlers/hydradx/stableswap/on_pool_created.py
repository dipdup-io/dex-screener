from itertools import combinations

from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.service.dex.stableswap.stableswap_service import get_pair_id
from dex_screener.service.dex.stableswap.stableswap_service import get_pool_account
from dex_screener.types.hydradx.substrate_events.stableswap_pool_created import StableswapPoolCreatedPayload
from service.dex.stableswap.stableswap_service import get_pool_pk


async def on_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapPoolCreatedPayload],
) -> None:
    lp_token_id = event.payload['pool_id']
    account = await get_pool_account(event.payload['pool_id'], event.data.level)

    pool = await Pool.create(
        account=get_pool_pk(account, lp_token_id),
        dex_key=DexKey.StableSwap,
        dex_pool_id=lp_token_id,
        lp_token_id=lp_token_id,
        # NOTE: Set later in the same block
        shares='0',
    )
    ctx.logger.info('StableSwap Pool registered: %r.', pool)

    pool_assets_id: list[int] = list(event.payload['assets'])
    pool_assets_id.append(pool.lp_token_id)

    for asset_a_id, asset_b_id in combinations(pool_assets_id, 2):
        pair_id = get_pair_id(pool, asset_a_id, asset_b_id)

        event_info = DexScreenerEventInfoDTO.from_event(event)

        pair = await Pair.create(
            id=pair_id,
            dex_key=DexKey.StableSwap,
            asset_0_id=min(asset_a_id, asset_b_id),
            asset_1_id=max(asset_a_id, asset_b_id),
            pool=pool,
            created_at_block_id=event_info.block_id,
            created_at_tx_id=event_info.tx_index,
            fee_bps=event.payload['fee'],
        )
        ctx.logger.info('Pair registered in pool %r: %r.', pool, pair)

    # pool_assets: list[Asset] = await Asset.filter(id__in=pool_assets_id)
    # await pool.assets.add(*pool_assets)  # type: ignore[attr-defined]
    # ctx.logger.info('Assets added to pool %r: %s.', pool, pool_assets)
