from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.xyk_pool_created import XYKPoolCreatedPayload


async def on_xyk_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKPoolCreatedPayload],
) -> None:
    pool = models.Pool(
        id=event.payload['pool'],
        who=event.payload['who'],
        asset_a=event.payload['asset_a'],
        asset_b=event.payload['asset_b'],
        initial_shares_amount=event.payload['initial_shares_amount'],
        share_token=event.payload['share_token'],
    )
    await pool.save()
