from dipdup.context import HookContext

from dex_screener.models import Asset


async def on_reindex(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_reindex')

    assets = []
    client = ctx.get_substrate_datasource('node')._interface
    asset_map = await client.query_map('AssetRegistry', 'Assets')
    async for k, v in asset_map:
        name = v.value.get('name', None)
        if name is not None and not name.isalnum():
            name = '0x' + name.encode().hex()
        assets.append(
            Asset(
                id=k.value,
                name=name,
                symbol=v.value.get('symbol', None),
                decimals=v.value.get('decimals', 0),
                asset_type=v.value.get('asset_type', None),
                updated_at_block_id=0,
            )
        )
    await Asset.bulk_create(assets)
