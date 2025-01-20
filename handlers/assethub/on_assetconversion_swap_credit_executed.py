from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.asset_conversion_swap_credit_executed import (
    AssetConversionSwapCreditExecutedPayload,
)


async def on_assetconversion_swap_credit_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionSwapCreditExecutedPayload],
) -> None:
    try:
        event.payload['path'] = models.fix_multilocation(event.payload['path'])
    except KeyError:
        if 'GlobalConsensus' not in str(event.payload['path']):
            raise
        ctx.logger.error('FIXME: GlobalConsensus path %s', event.payload['path'])
        return

    path = event.payload['path']
    if len(path) != 2:
        ctx.logger.error('FIXME: too many path elements %s', path)
        return

    path_from, path_to = path[0][0], path[1][0]

    if path_from['interior'] == 'Here':
        asset_0_id = -1
    elif 'X1' in path_from['interior']:
        ctx.logger.warning('FIXME: X1 path %s', path_from)
        return
    else:
        asset_0_id = path_from['interior']['X2'][-1]['GeneralIndex']

    if path_to['interior'] == 'Here':
        asset_1_id = -1
    elif 'X1' in path_to['interior']:
        ctx.logger.warning('FIXME: X1 path %s', path_to)
        return
    else:
        asset_1_id = path_to['interior']['X2'][-1]['GeneralIndex']

    assert asset_0_id != asset_1_id

    asset_0 = await models.Asset.get_or_none(id=asset_0_id) or models.Asset()
    asset_1 = await models.Asset.get_or_none(id=asset_1_id) or models.Asset()

    ctx.logger.info('Processing swap:')
    ctx.logger.info('<<< %s', asset_0.get_repr())
    ctx.logger.info('>>> %s', asset_1.get_repr())
