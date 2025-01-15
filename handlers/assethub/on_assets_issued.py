from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_issued import AssetsIssuedPayload


async def on_assets_issued(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsIssuedPayload],
) -> None:
    print(event.payload)
