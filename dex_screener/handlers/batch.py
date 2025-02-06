from collections.abc import Iterable
from typing import TYPE_CHECKING

from dipdup.context import HandlerContext
from dipdup.index import MatchedHandler

if TYPE_CHECKING:
    from dipdup.datasources.substrate_subscan import SubstrateSubscanDatasource


async def batch(
    ctx: HandlerContext,
    handlers: Iterable[MatchedHandler],
) -> None:
    from dex_screener.models import Block

    batch_levels = []
    for handler in handlers:
        if handler.level not in batch_levels:
            try:
                timestamp = handler.args[0].data.header['timestamp'] // 1000
            except (KeyError, AttributeError, ValueError):
                subscan: SubstrateSubscanDatasource = ctx.get_substrate_datasource('subscan')
                block_data = await subscan.request('post', 'scan/block', json={'block_num': handler.level})
                timestamp = block_data['data']['block_timestamp']
            block = await Block.create(
                level=handler.level,
                timestamp=timestamp,
            )
            batch_levels.append(handler.level)

        await ctx.fire_matched_handler(handler)

    if block is not None:
        await block.fetch_related('dex_assets', 'dex_pairs', 'dex_swap_events')
        if all(
            [
                not block.dex_assets.related_objects,
                not block.dex_pairs.related_objects,
                not block.dex_swap_events.related_objects,
            ]
        ):
            await block.delete()
