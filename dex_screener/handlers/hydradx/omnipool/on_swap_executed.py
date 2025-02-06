from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.service.dex.omnipool.omnipool_service import OmnipoolService
from dex_screener.types.hydradx.substrate_events.omnipool_buy_executed import OmnipoolBuyExecutedPayload
from dex_screener.types.hydradx.substrate_events.omnipool_sell_executed import OmnipoolSellExecutedPayload


async def on_swap_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolBuyExecutedPayload | OmnipoolSellExecutedPayload],
) -> None:
    await OmnipoolService.register_swap(event)
