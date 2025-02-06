from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.service.dex.isolated_pool.isolated_pool_service import IsolatedPoolService
from dex_screener.types.hydradx.substrate_events.xyk_buy_executed import XYKBuyExecutedPayload
from dex_screener.types.hydradx.substrate_events.xyk_sell_executed import XYKSellExecutedPayload


async def on_swap_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKBuyExecutedPayload | XYKSellExecutedPayload],
) -> None:
    await IsolatedPoolService.register_swap(event)
