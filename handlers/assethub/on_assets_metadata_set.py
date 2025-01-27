from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.assets_metadata_set import AssetsMetadataSetPayload


async def on_assets_metadata_set(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetsMetadataSetPayload],
) -> None: ...
