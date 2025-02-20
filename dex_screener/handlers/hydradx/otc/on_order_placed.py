from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.service.dex.otc.otc_service import OTCService
from dex_screener.types.hydradx.substrate_events.otc_placed import OTCPlacedPayload


async def on_order_placed(
    ctx: HandlerContext,
    event: SubstrateEvent[OTCPlacedPayload],
) -> None:
    await OTCService.register_order(event)
