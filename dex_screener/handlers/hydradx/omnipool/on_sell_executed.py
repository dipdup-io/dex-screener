from dex_screener.models import Event
from dex_screener.types.hydradx.substrate_events.omnipool_sell_executed import OmnipoolSellExecutedPayload
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent


async def on_sell_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolSellExecutedPayload],
) -> None:
    await Event.create(
        who=event.data.args['who'],
        asset_in=event.data.args['assetIn'],
        asset_out=event.data.args['assetOut'],
        amount_in=event.data.args['amountIn'],
        amount_out=event.data.args['amountOut'],
    )
