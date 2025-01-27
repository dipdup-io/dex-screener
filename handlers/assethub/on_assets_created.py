from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_created import AssetsCreatedPayload


async def on_assets_created(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsCreatedPayload],
) -> None: ...
