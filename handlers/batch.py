from __future__ import annotations

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING

from dex_screener.models import Block

if TYPE_CHECKING:
    from dipdup.context import HandlerContext
    from dipdup.index import MatchedHandler


async def batch(
    ctx: HandlerContext,
    handlers: tuple[MatchedHandler, ...],
) -> None:
    batch_levels: set[int] = set()
    for handler in handlers:
        if handler.level not in batch_levels:
            try:
                timestamp = int(handler.args[0].data.header_extra['timestamp'] // 1000)  # type: ignore[index]
            except (KeyError, AttributeError, ValueError, TypeError):
                timestamp = None

            await Block.create(
                level=handler.level,
                timestamp=timestamp,
            )
            batch_levels.add(handler.level)

        try:
            await ctx.fire_matched_handler(handler)
        except Exception as exception:
            ctx.logger.error('Event Processing Error for: %s.', handler.args)
            raise exception

    if RuntimeFlag.blocks_refresh_condition():
        ctx.logger.info('Processing refresh `dex_block`...')
        await ctx.execute_sql_script('refresh_blocks.01_drop_unused_blocks')

        for _ in range(10):
            levels: list[int] = (
                await Block.filter(timestamp__isnull=True).order_by('level').limit(100).values_list('level', flat=True)  # type: ignore[assignment]
            )
            if len(levels) == 0:
                break
            request_payload = {
                'query': ' '.join(
                    [
                        'query { blocks(where: {height_in:',
                        str(levels),
                        '}) { height timestamp } }',
                    ]
                ),
            }

            explorer = ctx.get_http_datasource('explorer')
            response = await explorer.request('post', 'graphql', json=request_payload)

            blocks = [
                Block(
                    level=block_data['height'],
                    timestamp=datetime.fromisoformat(block_data['timestamp']).timestamp(),
                )
                for block_data in response['data']['blocks']
            ]
            if len(blocks) == 0:
                ctx.logger.info('No blocks found for levels: %s.', levels)
                break

            await Block.bulk_update(objects=blocks, fields=['timestamp'])

        await ctx.execute_sql_script('refresh_blocks.00_refresh_latest_block')

        next_refresh_at = RuntimeFlag.blocks_set_next_refresh()
        ctx.logger.info('Next blocks refresh is scheduled at %s.', next_refresh_at)


class RuntimeFlag:
    blocks_refresh_at: datetime = datetime.now(UTC)
    blocks_refresh_period: timedelta = timedelta(seconds=60)

    @classmethod
    def blocks_refresh_condition(cls) -> bool:
        return datetime.now(UTC) >= cls.blocks_refresh_at

    @classmethod
    def blocks_set_next_refresh(cls) -> datetime:
        cls.blocks_refresh_at = datetime.now(UTC).replace(microsecond=0) + cls.blocks_refresh_period
        return cls.blocks_refresh_at
