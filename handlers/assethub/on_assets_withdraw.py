from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_withdraw import AssetsWithdrawPayload


async def on_assets_withdraw(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsWithdrawPayload],
) -> None: ...
