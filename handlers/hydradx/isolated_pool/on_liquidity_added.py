from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import AssetPoolReserve
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.types.hydradx.substrate_events.xyk_liquidity_added import XYKLiquidityAddedPayload


async def on_liquidity_added(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKLiquidityAddedPayload],
) -> None:
    ...