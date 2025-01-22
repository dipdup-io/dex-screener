from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as m
from dex_screener.models.asset import OMNIPOOL_LP_ASSET_ID
from dex_screener.types.hydradx.substrate_events.omnipool_position_updated import OmnipoolPositionUpdatedPayload
from models.block import upsert_block_model
from models.pair import upsert_pair_model


async def on_omnipool_position_updated(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolPositionUpdatedPayload],
) -> None:
    position_id = event.payload['position_id']
    owner = event.payload['owner']
    asset_id = event.payload['asset']
    amount = event.payload['amount']
    shares = event.payload['shares']
    price = event.payload['price']

    # get position
    pos_dict = {
        'position_id': position_id,
        'owner': owner,
        'asset': asset_id,
        'amount': amount,
        'shares': shares,
        'price': price,
    }
    position, created = await m.OmnipoolPositions.get_or_create(position_id=position_id, defaults=pos_dict)
    if created:
        ctx.logger.warning('Position not found, creating new')

    # save block
    await upsert_block_model(
        event.data.header['number'],
        event.data.header_extra['timestamp'] if event.data.header_extra else None,
    )

    pair_id = await upsert_pair_model(OMNIPOOL_LP_ASSET_ID, asset_id)

    # emit exit event
    exit_event = m.Event(
        event_type='exit',
        composite_pk=f'{event.data.block_number}-{event.data.extrinsic_index}-{event.data.index}',
        txn_id=f'{event.data.block_number}-{event.data.extrinsic_index}-{event.data.index}',
        txn_index=event.data.extrinsic_index or event.data.index,
        event_index=event.data.index,
        maker=owner,
        pair_id=pair_id,
        # NOTE: new position contains numbers after liqudity was removed
        amount_0=amount if created else amount - position.amount,
        amount_1=shares if created else shares - position.shares,
        # TODO: calculate price?
        price_native=price,
        # TODO: get and update pool fields
        # reserves_asset_0
        # reserves_asset_1
    )
    await exit_event.save()

    position.update_from_dict(pos_dict)
