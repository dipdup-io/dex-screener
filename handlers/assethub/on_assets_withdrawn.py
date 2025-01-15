from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_withdrawn import AssetsWithdrawnPayload


async def on_assets_withdrawn(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsWithdrawnPayload],
) -> None:
    print(event.payload)
