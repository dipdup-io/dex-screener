from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_metadata_cleared import AssetsMetadataClearedPayload
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent


async def on_assets_metadata_cleared(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsMetadataClearedPayload],
) -> None:
    raise NotImplementedError