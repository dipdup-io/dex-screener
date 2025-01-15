from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_created import AssetsCreatedPayload
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent


async def on_assets_created(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsCreatedPayload],
) -> None:
    ...