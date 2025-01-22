from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as m
from dex_screener.types.hydradx.substrate_events.omnipool_position_created import OmnipoolPositionCreatedPayload
from models.asset import OMNIPOOL_LP_ASSET_ID
from models.block import upsert_block_model
from models.pair import upsert_pair_model


async def on_omnipool_position_created(
    ctx: HandlerContext,
    event: SubstrateEvent[OmnipoolPositionCreatedPayload],
) -> None:
    position_id = event.payload['position_id']
    owner = event.payload['owner']
    asset_id = event.payload['asset']
    amount = event.payload['amount']
    shares = event.payload['shares']
    price = event.payload['price']

    # save position
    position_model = m.OmnipoolPositions(
        position_id=position_id,
        owner=owner,
        asset=asset_id,
        amount=amount,
        shares=shares,
        price=price,
    )
    await position_model.save()

    # save block
    await upsert_block_model(
        event.data.header['number'],
        event.data.header_extra['timestamp'] if event.data.header_extra else None,
    )

    pair_id = await upsert_pair_model(OMNIPOOL_LP_ASSET_ID, asset_id)

    # emit join event
    join_event = m.Event(
        event_type='join',
        composite_pk=f'{event.data.block_number}-{event.data.extrinsic_index}-{event.data.index}',
        txn_id=f'{event.data.block_number}-{event.data.extrinsic_index}-{event.data.index}',
        txn_index=event.data.extrinsic_index or event.data.index,
        event_index=event.data.index,
        maker=owner,
        pair_id=pair_id,
        amount_0=amount,
        amount_1=shares,
        # TODO: calculate price?
        price_native=price,
        # TODO: get and update pool fields
        # reserves_asset_0
        # reserves_asset_1
    )
    await join_event.save()
