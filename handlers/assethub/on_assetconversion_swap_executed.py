from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener import models as models
from dex_screener.types.assethub.substrate_events.asset_conversion_swap_executed import (
    AssetConversionSwapExecutedPayload,
)


# WARNING  dex_screener.handlers.assethub.on_assetconversion_swap_executed SwapExecuted: {'who': '0x766b24858cbbc7be7fcae776feb14688e6d860e5566958aa4ef8c7ab8d792e1f', 'path': [[{'parents': 1, 'interior': {'__kind': 'Here'}}, 1000000000], [{'parents': 0, 'interior': {'__kind': 'X2', 'value': [{'__kind': 'PalletInstance', 'value': 50}, {'__kind': 'GeneralIndex', 'value': '1984'}]}}, 737624]], 'send_to': '0x766b24858cbbc7be7fcae776feb14688e6d860e5566958aa4ef8c7ab8d792e1f', 'amount_in': 1000000000, 'amount_out': 737624}
def extract_path(payload: AssetConversionSwapExecutedPayload) -> tuple: ...


async def on_assetconversion_swap_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[AssetConversionSwapExecutedPayload],
) -> None:

    ctx.logger.warning('SwapExecuted: %s', event.payload)
    # raise NotImplementedError
