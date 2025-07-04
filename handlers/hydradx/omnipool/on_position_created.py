from types.hydradx.substrate_events.omnipool_position_created import OmnipoolPositionCreatedPayload

from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from models import DexEvent
from models import DexOmnipoolPosition
from models import Pair
from service.dex.omnipool.const import OMNIPOOL_HUB_ASSET_ID
from service.dex.omnipool.omnipool_service import OmnipoolService
from service.event.const import DexScreenerEventType
from service.event.entity.dto import DexScreenerEventDataDTO
from service.event.entity.join_exit.dto import JoinExitEventMarketDataDTO
from service.event.entity.join_exit.dto import JoinExitEventPoolDataDTO


async def on_position_created(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolPositionCreatedPayload],
) -> None:
    # save omnipool position
    # create join event (and fetch data for event)

    position = await DexOmnipoolPosition.create(
        position_id=event.payload['position_id'],
        owner=event.payload['owner'],
        asset_id=event.payload['asset'],
        amount=event.payload['amount'],
        shares=event.payload['shares'],
        created=True,
    )

    event_data = DexScreenerEventDataDTO(
        event_index=event.data.index,
        name=event.data.name,
        block_id=event.data.level,
        tx_index=event.data.extrinsic_index if event.data.extrinsic_index is not None else 0,
    )

    pair_id = OmnipoolService.get_pair_id(position.asset_id, OMNIPOOL_HUB_ASSET_ID)
    pool_data = JoinExitEventPoolDataDTO(
        pair_id=pair_id,
    )

    pair = await Pair.get(id=pair_id).prefetch_related('asset_0', 'asset_1')
    amount_0 = pair.asset_0.from_minor(position.amount)
    amount_1 = pair.asset_1.from_minor(position.shares)
    if pair.asset_0.id != position.asset_id:
        amount_0, amount_1 = amount_1, amount_0
    market_data = JoinExitEventMarketDataDTO(
        maker=position.owner,
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
