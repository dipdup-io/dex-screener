from dipdup.context import HookContext

from dex_screener.models import CachedPools
from dex_screener.models import Pool


async def on_restart(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_restart')
    CachedPools.account_list = set(await Pool.all().values_list('account', flat=True))
