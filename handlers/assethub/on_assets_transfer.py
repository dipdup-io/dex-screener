from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_transfer import AssetsTransferPayload
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent


async def on_assets_transfer(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsTransferPayload],
) -> None:
    ...