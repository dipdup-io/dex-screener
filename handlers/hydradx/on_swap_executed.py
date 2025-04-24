from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.service.event.event_service import DexScreenerEventService
from dex_screener.service.event.exception import RegisterDexScreenerEventError
from dex_screener.service.event.exception import UnsuitableEventMatchedError
from dex_screener.types.hydradx.substrate_events.omnipool_buy_executed import OmnipoolBuyExecutedPayload
from dex_screener.types.hydradx.substrate_events.omnipool_sell_executed import OmnipoolSellExecutedPayload
from dex_screener.types.hydradx.substrate_events.xyk_buy_executed import XYKBuyExecutedPayload
from dex_screener.types.hydradx.substrate_events.xyk_sell_executed import XYKSellExecutedPayload

XYKSwapPayload = XYKBuyExecutedPayload | XYKSellExecutedPayload
OmnipoolSwapPayload = OmnipoolBuyExecutedPayload | OmnipoolSellExecutedPayload

SwapPayload = XYKSwapPayload | OmnipoolSwapPayload


async def on_swap_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[SwapPayload],
) -> None:
    try:
        swap_event_record = await DexScreenerEventService.register_swap(event)
        ctx.logger.info('Swap Event registered: %r.', swap_event_record)
    except UnsuitableEventMatchedError as exception:
        ctx.logger.info('Swap Event ignored: %s.', exception)
    except RegisterDexScreenerEventError as exception:
        ctx.logger.error('Swap Event processing error: %s.', exception)
