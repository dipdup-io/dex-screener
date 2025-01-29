from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.asset_conversion_swap_credit_executed import (
    AssetConversionSwapCreditExecutedPayload,
)
from models import save_unprocesssed_payload


async def on_assetconversion_swap_credit_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionSwapCreditExecutedPayload],
) -> None:
    path = event.payload['path']
    if len(path) != 2:
        ctx.logger.error('FIXME: too many path elements %s', path)
        await save_unprocesssed_payload(event.payload, 'too many path elements')
        return

    path_from, path_to = path[0][0], path[1][0]

    if path_from['interior'] == 'Here':
        asset_0_id = -1
    else:
        try:
            asset_0_id = path_from['interior']['X2'][-1]['GeneralIndex']
        except (KeyError, TypeError):
            msg = 'not a X2 path'
            ctx.logger.warning('%s %s', msg, path_from)
            await save_unprocesssed_payload(event.payload, msg)
            return

    if path_to['interior'] == 'Here':
        asset_1_id = -1
    else:
        try:
            asset_1_id = path_to['interior']['X2'][-1]['GeneralIndex']
        except (KeyError, TypeError):
            msg = 'not a X2 path'
            ctx.logger.warning('%s %s', msg, path_to)
            await save_unprocesssed_payload(event.payload, msg)
            return

    assert asset_0_id != asset_1_id

    asset_0 = await models.Asset.get_or_none(id=asset_0_id)
    asset_1 = await models.Asset.get_or_none(id=asset_1_id)

    ctx.logger.info('Processing swap:')
    ctx.logger.info('<<< %s', asset_0.get_repr())
    ctx.logger.info('>>> %s', asset_1.get_repr())

    pair_id = models.get_pair_id(asset_0_id, asset_1_id)
    pair, _ = await models.Pair.get_or_create(
        id=pair_id,
        defaults={
            'asset_0_id': asset_0_id,
            'asset_1_id': asset_1_id,
            'dex_key': 'assethub',
        },
    )
    ctx.logger.info('Pair %s: %s', 'updated' if _ else 'created', pair.id)

    event_model = models.Event(
        event_type='swap',
        composite_pk=f'{event.data.block_number}-{event.data.extrinsic_index}-{event.data.index}',
        # NOTE: take caution, event index is used due to extrinsic index being null
        txn_id=f'{event.data.block_number}-{event.data.extrinsic_index}-{event.data.index}',
        txn_index=event.data.extrinsic_index or event.data.index,
        event_index=event.data.index,
        # FIXME: Who?
        # maker=event.data.call_address[0],  # ???
        maker='FIXME',
        pair_id=pair_id,
        asset_0_in=event.payload['amount_in'],
        asset_1_out=event.payload['amount_out'],
        # TODO: get and update pool fields
        # FIXME: calculate priceNative
        price_native=0,
    )
    await event_model.save()
    ctx.logger.info('Event created: %s', event_model.composite_pk)
