from dipdup.context import HookContext


async def refresh_blocks(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('refresh_blocks')