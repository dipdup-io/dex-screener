from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.xyk_buy_executed import XYKBuyExecutedPayload


async def on_xyk_buy_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKBuyExecutedPayload],
) -> None:
    pool = await models.Pool.filter(id=event.payload['pool']).get()
    asset_in = await models.Asset.filter(id=hex(event.payload['asset_in'])).get()
    asset_out = await models.Asset.filter(id=hex(event.payload['asset_out'])).get()
