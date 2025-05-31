from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import DoesNotExist
from dex_screener.models import DexEvent
from dex_screener.models import DexOmnipoolPosition
from dex_screener.models import Pair
from dex_screener.service.dex.omnipool.const import OMNIPOOL_HUB_ASSET_ID
from dex_screener.service.dex.omnipool.omnipool_service import OmnipoolService
from dex_screener.service.event.const import DexScreenerEventType
from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO
from dex_screener.service.event.entity.join_exit.dto import JoinExitEventMarketDataDTO
from dex_screener.service.event.entity.join_exit.dto import JoinExitEventPoolDataDTO
from dex_screener.types.hydradx.substrate_events.omnipool_position_destroyed import OmnipoolPositionDestroyedPayload

from dipdup.models import Meta

async def on_position_destroyed(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolPositionDestroyedPayload],
) -> None:
    try:
        position: DexOmnipoolPosition = await DexOmnipoolPosition.get(
            position_id=event.payload['position_id'],
        )
    except DoesNotExist:
        ctx.logger.warning(
            'Position %s not found in the database, skipping `position_destroyed` event',
            event.payload['position_id'],
        )
        await Meta.create(
            key=f'fail_{event.name}_{event.data.block_id}-{event.data.event_index}',
            value=event.payload,
        )
        return

    event_data = DexScreenerEventDataDTO(
        event_index=event.data.index,
        name=event.data.name,
        block_id=event.data.level,
        tx_index=event.data.extrinsic_index if event.data.extrinsic_index is not None else 0,
    )

    pool_data = JoinExitEventPoolDataDTO(
        pair_id=OmnipoolService.get_pair_id(position.asset_id, OMNIPOOL_HUB_ASSET_ID),
    )
    pair: Pair = await Pair.get(id=pool_data.pair_id).prefetch_related('asset_0', 'asset_1')
    amount_list = [
        pair.asset_0.from_minor(position.amount),
        pair.asset_1.from_minor(position.shares),
    ]
    if pair.asset_0.id != position.asset_id:
        amount_list.reverse()

    market_data = JoinExitEventMarketDataDTO(
        maker=position.owner,
        amount_0=str(amount_list[0]),
        amount_1=str(amount_list[1]),
    )

    fields = {
        **event_data.model_dump(),
        **pool_data.model_dump(),
        **market_data.model_dump(),
    }
    fields.update({'event_type': DexScreenerEventType.Exit})

    await DexEvent.create(**fields)
