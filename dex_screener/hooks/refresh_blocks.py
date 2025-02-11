import datetime

from dipdup.context import HookContext

from dex_screener.models import Block


async def refresh_blocks(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('refresh_blocks')

    levels: list[int] = await Block.filter(timestamp__isnull=True).order_by('level').limit(100).values_list('level', flat=True)
    if len(levels) == 0:
        return
    request_payload = {
        'query': ' '.join([
            'query { blocks(where: {height_in:',
            str(levels),
            '}) { height timestamp } }',
        ]),
    }

    explorer = ctx.get_http_datasource('explorer')
    response = await explorer.request('post', 'graphql', json=request_payload)

    blocks = [
        Block(
            level=block_data['height'],
            timestamp=datetime.datetime.fromisoformat(block_data['timestamp']).timestamp(),
        ) for block_data in response['data']['blocks']
    ]

    await Block.bulk_update(
        objects=blocks, fields=['timestamp']
    )
