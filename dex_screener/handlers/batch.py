from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from dipdup.context import HandlerContext
    from dipdup.datasources.substrate_subscan import SubstrateSubscanDatasource
    from dipdup.index import MatchedHandler


async def batch(
    ctx: HandlerContext,
    handlers: Iterable[MatchedHandler],
) -> None:
    batch_levels = []
    for handler in handlers:
        from dipdup.indexes.substrate_events.index import SubstrateEventsIndex
        if handler.level not in batch_levels and isinstance(handler.index, SubstrateEventsIndex):
            try:
                timestamp = int(handler.args[0].data.header_extra['timestamp'] // 1000)
            except (KeyError, AttributeError, ValueError):
                subscan: SubstrateSubscanDatasource = ctx.get_substrate_datasource('subscan')
                block_data = await subscan.request('post', 'scan/block', json={'block_num': handler.level})
                timestamp = int(block_data['data']['block_timestamp'])

            from dex_screener.models import Block
            await Block.create(
                level=handler.level,
                timestamp=timestamp,
            )
            batch_levels.append(handler.level)

        await ctx.fire_matched_handler(handler)
