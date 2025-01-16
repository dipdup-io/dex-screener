from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_transferred import AssetsTransferredPayload


async def on_assets_transferred(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsTransferredPayload],
) -> None:
    pass
