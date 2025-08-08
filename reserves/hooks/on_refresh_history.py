from time import time

from dipdup.context import HookContext

from reserves.handlers.batch import RuntimeFlag


async def on_refresh_history(
    ctx: HookContext,
) -> None:
    # NOTE
    if RuntimeFlag.realtime:
        ctx.logger.debug('skipping, realtime updates are enabled')
        return

    if not RuntimeFlag.history_refresh_condition():
        ctx.logger.debug('skipping, no history refresh condition met')
        return

    ctx.logger.info('Processing refresh of `balance_history` and `supply_history`...')

    refresh_start = time()
    await ctx.execute_sql_script('on_refresh_history')
    refresh_duration = time() - refresh_start

    ctx.logger.debug('Balance and supply history updated in %.2f seconds', refresh_duration)
    RuntimeFlag.history_set_next_refresh(ctx)
