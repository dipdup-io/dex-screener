from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from scalecodec import ss58_decode

from dex_screener.models import DexOmnipoolPosition
from dex_screener.types.hydradx.substrate_events.omnipool_position_created import OmnipoolPositionCreatedPayload


async def on_position_created(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolPositionCreatedPayload],
) -> None:
    if not event.payload['owner'].startswith('0x'):
        event.payload['owner'] = f'0x{ss58_decode(event.payload["owner"])}'

    await DexOmnipoolPosition.create(
        position_id=event.payload['position_id'],
        owner=event.payload['owner'],
        asset_id=event.payload['asset'],
        amount=event.payload['amount'],
        shares=event.payload['shares'],
    )
