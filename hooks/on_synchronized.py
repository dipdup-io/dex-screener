from datetime import timedelta

from dipdup.context import HookContext

from dex_screener.handlers.batch import RuntimeFlag


async def on_synchronized(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_synchronized')

    blocks_refresh_period_params = ctx.config.custom['realtime_blocks_refresh_period']
    RuntimeFlag.blocks_refresh_period = timedelta(**blocks_refresh_period_params)
