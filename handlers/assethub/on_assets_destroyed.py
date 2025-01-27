from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_destroyed import AssetsDestroyedPayload


async def on_assets_destroyed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsDestroyedPayload],
) -> None: ...
