from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_deposit import AssetsDepositPayload


async def on_assets_deposit(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsDepositPayload],
) -> None: ...
