from dipdup.context import HookContext
from scalecodec import ss58_decode  # type: ignore[import-untyped]

from reserves.models import BalanceUpdateEvent


async def on_reindex(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_reindex')

    client = ctx.get_substrate_datasource('node')._interface  # type: ignore[union-attr]

    block_hash = await client.get_block_hash(0)
    account_map = await client.query_map('System', 'Account', block_hash=block_hash, page_size=1000)
    counter = 0
    initial_balances_list = []
    async for account, account_info in account_map:
        initial_balance = sum(
            [
                account_info.value['data']['free'],
                account_info.value['data']['reserved'],
            ]
        )
        if initial_balance == 0:
            continue
        counter += 1
        account = f'0x{ss58_decode(account.value)}'
        asset_id = 0

        initial_balances_list.append(
            BalanceUpdateEvent(
                id=counter,
                asset_account=BalanceUpdateEvent.group_key(asset_id, account),
                asset_id=asset_id,
                account=account,
                balance_update=initial_balance,
            )
        )
    await BalanceUpdateEvent.bulk_create(initial_balances_list)
