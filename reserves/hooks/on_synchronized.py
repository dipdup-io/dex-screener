from dipdup.context import HookContext

from reserves.handlers.batch import RuntimeFlag


async def on_synchronized(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_synchronized')

    RuntimeFlag.synchronized = True
