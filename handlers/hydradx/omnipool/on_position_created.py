from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import DexEvent
from dex_screener.models import DexOmnipoolPosition
from dex_screener.models import Pair
from dex_screener.service.dex.omnipool.const import OMNIPOOL_HUB_ASSET_ID
from dex_screener.service.dex.omnipool.omnipool_service import OmnipoolService
from dex_screener.service.event.const import DexScreenerEventType
from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO
from dex_screener.service.event.entity.join_exit.dto import JoinExitEventMarketDataDTO
from dex_screener.service.event.entity.join_exit.dto import JoinExitEventPoolDataDTO
from dex_screener.types.hydradx.substrate_events.omnipool_position_created import OmnipoolPositionCreatedPayload
from dex_screener.utils import NotFound
from dex_screener.utils import get_reserves_by_pair


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
    pair = await Pair.get_or_none(id=pair_id).prefetch_related('asset_0', 'asset_1', 'pool')
    if not pair:
        pair = await OmnipoolService.register_pair_from_positions(event)

    try:
        reserves_0, reserves_1 = await get_reserves_by_pair(pair, event.data.level)
    except NotFound:
        reserves_0, reserves_1 = 0, 0

    pool_data = JoinExitEventPoolDataDTO(
        pair_id=pair_id,
        asset_0_reserve=pair.asset_0_amount(reserves_0),
        asset_1_reserve=pair.asset_1_amount(reserves_1),
    )

    if pair.asset_0.id == position.asset_id:
        amount_0, amount_1 = int(position.amount), int(position.shares)
    else:
        amount_0, amount_1 = int(position.shares), int(position.amount)

    market_data = JoinExitEventMarketDataDTO(
        maker=position.owner,
        amount_0=pair.asset_0_amount(amount_0),
        amount_1=pair.asset_1_amount(amount_1),
    )

    fields = {
        **event_data.model_dump(),
        **pool_data.model_dump(),
        **market_data.model_dump(),
        'event_type': DexScreenerEventType.Join,
    }
    await DexEvent.create(**fields)
