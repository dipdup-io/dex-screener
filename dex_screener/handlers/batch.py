from collections.abc import Iterable

from dipdup.context import HandlerContext
from dipdup.index import MatchedHandler


async def batch(
    ctx: HandlerContext,
    handlers: Iterable[MatchedHandler],
) -> None:
    from dex_screener.models import Block

    batch_levels = []
    for handler in handlers:
        if handler.level not in batch_levels:
            block = await Block.create(
                level=handler.level,
                timestamp=handler.args[0].data.header['timestamp'] // 1000,
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
