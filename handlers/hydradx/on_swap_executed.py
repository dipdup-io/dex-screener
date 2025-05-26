from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.service.event.event_service import DexScreenerEventService
from dex_screener.service.event.exception import RegisterDexScreenerEventError
from dex_screener.service.event.exception import UnsuitableEventMatchedError
from dex_screener.types.hydradx.substrate_events.broadcast_swapped import BroadcastSwappedPayload
from dex_screener.types.hydradx.substrate_events.broadcast_swapped2 import BroadcastSwapped2Payload
from dex_screener.types.hydradx.substrate_events.broadcast_swapped3 import BroadcastSwapped3Payload


async def on_swap_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[BroadcastSwappedPayload | BroadcastSwapped2Payload | BroadcastSwapped3Payload],
) -> None:
    try:
        swap_event_record = await DexScreenerEventService.register_swap(event)
        ctx.logger.info('Swap Event registered: %r.', swap_event_record)
    except UnsuitableEventMatchedError as exception:
        ctx.logger.info('Swap Event ignored: %s.', exception)
    except RegisterDexScreenerEventError as exception:
        ctx.logger.error('Swap Event processing error: %s.', exception)
