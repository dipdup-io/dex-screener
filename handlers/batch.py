from collections.abc import Iterable

from dipdup.context import HandlerContext
from dipdup.index import MatchedHandler


async def batch(
    ctx: HandlerContext,
    handlers: Iterable[MatchedHandler],
) -> None:
    from dex_screener.models import Block

    for handler in handlers:
        await ctx.fire_matched_handler(handler)

    await Block.create(
        level=handler.level,
        timestamp=handler.args[0].data.header['timestamp'] // 1000,
    )
