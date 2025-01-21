import time

from dex_screener import models as m


async def upsert_block_model(block_number: int, block_timestamp: int | None = None) -> None:
    # FIXME: block_timestamp is not available from node
    block, created = await m.Block.get_or_create(
        block_number=block_number, defaults={'block_timestamp': block_timestamp, 'written_timestamp': int(time.time())}
    )
    if not created:
        await block.save()
