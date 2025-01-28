from dipdup.context import HookContext

# from dex_screener import models
# from models import NATIVE_ASSET_ID


async def on_restart(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql_script('on_restart')

    # model, created = await models.Asset.get_or_create(
    #     id=NATIVE_ASSET_ID,
    #     defaults={
    #         'name': ctx.config.custom['native_token']['name'],
    #         'symbol': ctx.config.custom['native_token']['symbol'],
    #         'metadata': {
    #             'decimals': ctx.config.custom['native_token']['decimals'],
    #         },
    #     },
    # )
    # if created:
    #     ctx.logger.info('Creating native asset: %s', model.get_repr())
