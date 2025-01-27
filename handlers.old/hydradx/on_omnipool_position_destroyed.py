from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import DoesNotExist

from dex_screener import models as m
from dex_screener.types.hydradx.substrate_events.omnipool_position_destroyed import OmnipoolPositionDestroyedPayload
from models.asset import OMNIPOOL_LP_ASSET_ID
from models.pair import upsert_pair_model


async def on_omnipool_position_destroyed(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolPositionDestroyedPayload],
) -> None:
    position_id = event.payload['position_id']

    try:
        position = await m.OmnipoolPositions.get(position_id=position_id)
    except DoesNotExist:
        error_str = f'Position not found: {position_id}, block: {event.data.header["number"]}'
        ctx.logger.error(error_str)
        return

    pair_id = await upsert_pair_model(OMNIPOOL_LP_ASSET_ID, position.asset)

    # emit exit event
    extrinsic_index = event.data.extrinsic_index or 0
    exit_event = m.Event(
        event_type='exit',
        composite_pk=f'{event.data.block_number}-{extrinsic_index}-{event.data.index}',
        txn_id=f'{event.data.block_number}-{extrinsic_index}-{event.data.index}',
        txn_index=extrinsic_index,
        event_index=event.data.index,
        maker=position.owner,
        pair_id=pair_id,
        # NOTE: new position contains numbers after liqudity was removed
        amount_0=position.amount,
        amount_1=position.shares,
        # TODO: calculate price?
        price_native=0,
        # TODO: get and update pool fields
        # reserves_asset_0
        # reserves_asset_1
    )
    await exit_event.save()
