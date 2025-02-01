import time
from collections.abc import Iterable

from dipdup.context import HandlerContext
from dipdup.index import MatchedHandler


async def batch(
    ctx: HandlerContext,
    handlers: Iterable[MatchedHandler],
) -> None:
    from dex_screener.models import Block

    for handler in handlers:
        # print(handler)
        await ctx.fire_matched_handler(handler)

    await Block.create(
        block_number=handler.level,
        block_timestamp=handler.args[0].data.header['timestamp'] // 1000,
        written_timestamp=int(time.time()),
    )
