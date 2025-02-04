from collections.abc import Iterable

from dipdup.context import HandlerContext
from dipdup.index import MatchedHandler

from models.block import upsert_block_model


async def batch(
    ctx: HandlerContext,
    handlers: Iterable[MatchedHandler],
) -> None:
    for handler in handlers:
        await ctx.fire_matched_handler(handler)

    event_data = handlers[0].args[0].data  # type: ignore
    block_number = event_data.header['number']
    timestamp = event_data.header_extra['timestamp'] if event_data.header_extra else None
    await upsert_block_model(block_number, int(timestamp / 1000))
