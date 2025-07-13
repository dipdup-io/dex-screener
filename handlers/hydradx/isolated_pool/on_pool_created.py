from typing import TYPE_CHECKING

from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import Asset
from dex_screener.models import AssetPoolReserve
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models.dex_fields import Account
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.types.hydradx.substrate_events.xyk_pool_created import XYKPoolCreatedPayload

if TYPE_CHECKING:
    from aiosubstrate import SubstrateInterface

# FIXME: Why?
XYK_GET_EXCHANGE_FEE_BPS = 30


async def on_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKPoolCreatedPayload],
) -> None:
    # NOTE: Pool can be destroyed and recreated later. We don't need to process this event because shares=0.
    account = Account(event.payload['pool'])
    pool, _ = await Pool.update_or_create(
        account=account,
        defaults={
            'dex_key': DexKey.IsolatedPool,
            'dex_pool_id': event.payload['pool'],
            'lp_token_id': event.payload['share_token'],
            'shares': event.payload['initial_shares_amount'],
        },
    )

    ctx.logger.info('Pool registered: %r.', pool)

    pair_id = pool.account
    asset_a = await Asset.get(id=event.payload['asset_a'])
    asset_b = await Asset.get(id=event.payload['asset_b'])
    event_info = DexScreenerEventInfoDTO.from_event(event)

    if not await Pair.exists(id=pair_id):
        pair = await Pair.create(
            id=pair_id,
            dex_key=DexKey.IsolatedPool,
            asset_0_id=min(asset_a.id, asset_b.id),
            asset_1_id=max(asset_a.id, asset_b.id),
            pool=pool,
            created_at_block_id=event_info.block_id,
            created_at_tx_id=event_info.tx_index,
            fee_bps=XYK_GET_EXCHANGE_FEE_BPS,
        )
        ctx.logger.info('Pair registered in pool %r: %r.', pool, pair)

        await pool.assets.add(asset_a, asset_b)  # type: ignore[attr-defined]
        ctx.logger.info('Pair Assets added to pool %r: %s, %s.', pool, asset_a, asset_b)

    await update_reserves(ctx, pool, event)

async def update_reserves(
    ctx: HandlerContext,
    pool: Pool,
    event: SubstrateEvent[XYKPoolCreatedPayload],
) -> None:
    asset_a = await Asset.get(id=event.payload['asset_a'])
    asset_b = await Asset.get(id=event.payload['asset_b'])
    # FIXME: We need to fetch initial pool transfers to calculate share prices later
    reserves_a_model = await AssetPoolReserve.get(pool=pool, asset=asset_a)
    reserves_b_model = await AssetPoolReserve.get(pool=pool, asset=asset_b)

    node = ctx.datasources['node']
    interface: SubstrateInterface = node._interface

    block_hash = await interface.get_block_hash(event.data.block_number)
    block_events = await interface.get_events(block_hash)

    transfers = {}
    for block_event in block_events:
        e = block_event.value
        if (e['module_id'], e['event_id']) == ('Tokens', 'Transfer'):
            if e['attributes']['to'] != interface.ss58_encode(pool.account):
                continue
            transfers[e['attributes']['currency_id']] = e['attributes']['amount']
        elif (e['module_id'], e['event_id']) == ('Balances', 'Transfer'):
            if e['attributes']['to'] != interface.ss58_encode(pool.account):
                continue
            transfers[0] = e['attributes']['amount']

    for asset_id, value in transfers.items():
        if asset_id == asset_a.id:
            reserves_a_model.reserve = str(asset_a.from_minor(value))
        elif asset_id == asset_b.id:
            reserves_b_model.reserve = str(asset_b.from_minor(value))

    assert len(transfers) == 2

    await reserves_a_model.save()
    await reserves_b_model.save()
