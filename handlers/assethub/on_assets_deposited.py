from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_deposited import AssetsDepositedPayload


async def on_assets_deposited(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsDepositedPayload],
) -> None: ...
