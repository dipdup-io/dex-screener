from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.types.hydradx.substrate_events.xyk_pool_created import XYKPoolCreatedPayload


async def on_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKPoolCreatedPayload],
) -> None:
    pair_id = event.payload['pool']
    if not await Pair.exists(id=pair_id):
        pair = await Pair.create(
            id=event.payload['pool'],
            dex_key=DexKey[event.data.header_extra['specName']],
            asset_0_id=min(event.payload['asset_a'], event.payload['asset_b']),
            asset_1_id=max(event.payload['asset_a'], event.payload['asset_b']),
            created_at_block_id=event.level,
            created_at_txn_id=event.data.header['hash'],
            # fee_bps
        )
        ctx.logger.info('Pair created: %s.', pair.id)
    else:
        ctx.logger.warning('Pair already exists: %s.', pair_id)
