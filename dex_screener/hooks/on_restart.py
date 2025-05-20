from datetime import timedelta

from dipdup.context import HookContext
from scalecodec import is_valid_ss58_address

from dex_screener.handlers.batch import RuntimeFlag
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models.dex_fields import Account


async def on_restart(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_restart')

    blocks_refresh_period_params = ctx.config.custom['syncing_blocks_refresh_period']
    RuntimeFlag.blocks_refresh_period = timedelta(**blocks_refresh_period_params)

    await validate_indexed_values(ctx)


async def validate_indexed_values(ctx: HookContext):
    pool_account_batch = []
    async for pool_record in Pool.all():
        pool_record: Pool
        validated_account = Account(pool_record.account)
        if str(pool_record.pk) != str(validated_account):
            pool_account_batch.append(('account', validated_account, 'account', pool_record.account))

    for params in pool_account_batch:
        await ctx.execute_sql_script('on_restart.fix_invalid_records.dex_pool', *params)
        ctx.logger.warning('Fixed dex_pool.%s field: set new value %s for %s = %s.', *params)

    pool_pool_id_batch = []
    async for pool_record in Pool.all():
        pool_record: Pool
        validated_account = Account(pool_record.account)
        try:
            if is_valid_ss58_address(pool_record.dex_pool_id):
                pool_pool_id_batch.append(('dex_pool_id', Account(pool_record.dex_pool_id), 'account', validated_account))
        except IndexError:
            pass

    for params in pool_pool_id_batch:
        await ctx.execute_sql_script('on_restart.fix_invalid_records.dex_pool', *params)
        ctx.logger.warning('Fixed dex_pool.%s field: set new value %s for %s = %s.', *params)

    pair_id_batch = []
    async for pair_record in Pair.all():
        pair_record: Pair

        try:
            if is_valid_ss58_address(pair_record.id):
                pair_id_batch.append(('id', Account(pair_record.id), 'id', pair_record.id))
        except IndexError:
            pass

    for params in pair_id_batch:
        await ctx.execute_sql_script('on_restart.fix_invalid_records.dex_pair', *params)
        ctx.logger.warning('Fixed pair_id.%s field: set new value %s for %s = %s.', *params)
