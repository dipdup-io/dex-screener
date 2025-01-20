from dipdup.context import HookContext

from dex_screener import models


async def on_restart(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_restart')

    model, created = await models.Asset.get_or_create(
        id=-1,
        defaults={
            'name': 'DOT',
            'symbol': 'DOT',
        },
    )
    if created:
        ctx.logger.info('Creating DOT asset: %s', model.get_repr())
