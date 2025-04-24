from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import DexOmnipoolPosition
from dex_screener.types.hydradx.substrate_events.omnipool_position_created import OmnipoolPositionCreatedPayload


async def on_position_created(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolPositionCreatedPayload],
) -> None:
    await DexOmnipoolPosition.create(
        position_id=event.payload['position_id'],
        owner=event.payload['owner'],
        asset_id=event.payload['asset'],
        amount=event.payload['amount'],
        shares=event.payload['shares'],
    )
