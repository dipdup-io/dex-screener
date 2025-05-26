from datetime import timedelta

from dipdup.context import HookContext

from reserves.handlers.batch import EventBuffer
from reserves.handlers.batch import RuntimeFlag


async def on_restart(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_restart')

    history_refresh_period_params = ctx.config.custom['history_refresh_period']
    RuntimeFlag.history_refresh_period = timedelta(**history_refresh_period_params)
    RuntimeFlag.history_set_next_refresh(ctx)

    EventBuffer.buffer_limit = ctx.config.custom['event_buffer']['buffer_limit']

    await ctx.execute_sql_script('on_restart')
