from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from scalecodec import ss58_decode

from dex_screener.models import DexEvent
from dex_screener.models import DexOmnipoolPosition
from dex_screener.models import Pair
from dex_screener.service.dex.omnipool.const import OMNIPOOL_HUB_ASSET_ID
from dex_screener.service.dex.omnipool.omnipool_service import OmnipoolService
from dex_screener.service.event.const import DexScreenerEventType
from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO
from dex_screener.service.event.entity.join_exit.dto import JoinExitEventMarketDataDTO
from dex_screener.service.event.entity.join_exit.dto import JoinExitEventPoolDataDTO
from dex_screener.types.hydradx.substrate_events.omnipool_token_added import OmnipoolTokenAddedPayload


async def on_token_added(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolTokenAddedPayload],
) -> None:
    pool = await OmnipoolService.get_pool()
    await OmnipoolService.register_pair(pool, event)

    async for position in DexOmnipoolPosition.filter(created=False):
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

        if not market_data.maker.startswith('0x'):
            market_data.maker = f'0x{ss58_decode(market_data.maker)}'

        fields = {
            **event_data.model_dump(),
            **pool_data.model_dump(),
            **market_data.model_dump(),
        }
        fields.update({'event_type': DexScreenerEventType.Join})

        await DexEvent.create(**fields)

        position.created = True
        await position.save()
