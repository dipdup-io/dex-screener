import datetime
import threading

from dipdup.context import HookContext

from dex_screener.models import Block

refresh_blocks_lock = threading.Lock()


async def refresh_blocks(
    ctx: HookContext,
) -> None:
    if refresh_blocks_lock.locked():
        return

    with refresh_blocks_lock:
        await ctx.execute_sql_script('refresh_blocks.01_drop_unused_blocks')

        for _ in range(10):
            levels: list[int] = (
                await Block.filter(timestamp__isnull=True).order_by('-level').limit(100).values_list('level', flat=True)
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
                    timestamp=datetime.datetime.fromisoformat(block_data['timestamp']).timestamp(),
                )
                for block_data in response['data']['blocks']
            ]

            await Block.bulk_update(objects=blocks, fields=['timestamp'])

        # await ctx.execute_sql_script('refresh_blocks.02_vacuum_tables')

        await ctx.execute_sql_script('refresh_blocks.00_refresh_latest_block')
