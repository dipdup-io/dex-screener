from dipdup.context import HookContext
from scalecodec import ss58_decode

from reserves.models import BalanceUpdateEvent


async def on_reindex(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_reindex')

    client = ctx.get_substrate_datasource('node')._interface

    block_hash = await client.get_block_hash(0)
    account_map = await client.query_map('System', 'Account', block_hash=block_hash, max_results=1000)
    counter = 0
    for account, account_info in account_map:
        initial_balance = account_info.value['data']['free']
        if initial_balance == 0:
            continue
        counter += 1
        asset_id = 0
        account = f'0x{ss58_decode(account.value)}'

        await BalanceUpdateEvent.create(
            id=counter,
            account=account,
            asset_id=asset_id,
            balance_update=initial_balance,
        )
