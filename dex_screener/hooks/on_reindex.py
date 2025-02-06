from dipdup.context import HookContext

from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType
from dex_screener.models import Asset
from dex_screener.models import Block


async def on_reindex(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_reindex')
    await Block.create(level=0, timestamp=0)
    await Asset.create(id=0, name='HydraDX', symbol='HDX', decimals=10, asset_type=HydrationAssetType.Token, updated_at_block_id=0)
