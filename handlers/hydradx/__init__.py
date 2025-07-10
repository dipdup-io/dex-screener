from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO
from dex_screener.service.event.entity.join_exit.dto import JoinExitEventMarketDataDTO
from dex_screener.service.event.entity.join_exit.dto import JoinExitEventPoolDataDTO
from dex_screener.types.hydradx.substrate_events.lbp_liquidity_added import LBPLiquidityAddedPayload
from dex_screener.types.hydradx.substrate_events.lbp_liquidity_removed import LBPLiquidityRemovedPayload
from dex_screener.types.hydradx.substrate_events.xyk_liquidity_added import XYKLiquidityAddedPayload
from dex_screener.types.hydradx.substrate_events.xyk_liquidity_removed import XYKLiquidityRemovedPayload


async def liquidity_added(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKLiquidityAddedPayload | LBPLiquidityAddedPayload],
) -> None:
    from dex_screener.models import DexEvent
    from dex_screener.models import DexKey
    from dex_screener.models import DexScreenerEventType
    from dex_screener.models import Pair

    event_data = DexScreenerEventDataDTO(
        event_index=event.data.index,
        name=event.data.name,
        block_id=event.data.level,
        tx_index=event.data.extrinsic_index if event.data.extrinsic_index is not None else 0,
    )

    dex_key = DexKey.IsolatedPool if event.name.startswith('XYK') else DexKey.LBP
    asset_0 = min(int(event.payload['asset_a']), int(event.payload['asset_b']))
    asset_1 = max(int(event.payload['asset_a']), int(event.payload['asset_b']))

    pair = (
        await Pair.filter(
            dex_key=dex_key,
            asset_0_id=asset_0,
            asset_1_id=asset_1,
        )
        .prefetch_related('asset_0', 'asset_1')
        .get()
    )
    pool_data = JoinExitEventPoolDataDTO(
        pair_id=pair.id,
    )

    amount_0 = pair.asset_0.from_minor(event.payload['amount_a'])
    amount_1 = pair.asset_1.from_minor(event.payload['amount_b'])
    if pair.asset_0.id != asset_0:
        amount_0, amount_1 = amount_1, amount_0
    market_data = JoinExitEventMarketDataDTO(
        maker=event.payload['who'],
        amount_0=str(amount_0),
        amount_1=str(amount_1),
    )

    fields = {
        **event_data.model_dump(),
        **pool_data.model_dump(),
        **market_data.model_dump(),
        'event_type': DexScreenerEventType.Join,
    }
    await DexEvent.create(**fields)


async def liquidity_removed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKLiquidityRemovedPayload | LBPLiquidityRemovedPayload],
):
    from dex_screener.models import DexEvent
    from dex_screener.models import DexKey
    from dex_screener.models import DexScreenerEventType
    from dex_screener.models import Pair

    event_data = DexScreenerEventDataDTO(
        event_index=event.data.index,
        name=event.data.name,
        block_id=event.data.level,
        tx_index=event.data.extrinsic_index if event.data.extrinsic_index is not None else 0,
    )

    dex_key = DexKey.IsolatedPool if event.name.startswith('XYK') else DexKey.LBP
    asset_0 = min(int(event.payload['asset_a']), int(event.payload['asset_b']))
    asset_1 = max(int(event.payload['asset_a']), int(event.payload['asset_b']))

    pair = (
        await Pair.filter(
            dex_key=dex_key,
            asset_0_id=asset_0,
            asset_1_id=asset_1,
        )
        .prefetch_related('asset_0', 'asset_1')
        .get()
    )
    pool_data = JoinExitEventPoolDataDTO(
        pair_id=pair.id,
    )

    amount_0 = pair.asset_0.from_minor(event.payload['amount_a'])
    amount_1 = pair.asset_1.from_minor(event.payload['amount_b'])
    if pair.asset_0.id != asset_0:
        amount_0, amount_1 = amount_1, amount_0
    market_data = JoinExitEventMarketDataDTO(
        maker=event.payload['who'],
        amount_0=str(amount_0),
        amount_1=str(amount_1),
    )

    fields = {
        **event_data.model_dump(),
        **pool_data.model_dump(),
        **market_data.model_dump(),
        'event_type': DexScreenerEventType.Exit,
    }
    await DexEvent.create(**fields)
