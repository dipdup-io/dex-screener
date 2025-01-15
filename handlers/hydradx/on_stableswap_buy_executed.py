from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.types.hydradx.substrate_events.stableswap_buy_executed import StableswapBuyExecutedPayload


async def on_stableswap_buy_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[StableswapBuyExecutedPayload],
) -> None:
    ctx.logger.debug(str(event.payload))


#     await Event.create(
#         who=event.data.args['who'],
#         asset_in=event.data.args['assetIn'],
#         asset_out=event.data.args['assetOut'],
#         amount_in=event.data.args['amountIn'],
#         amount_out=event.data.args['amountOut'],
#     )
