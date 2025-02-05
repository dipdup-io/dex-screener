from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from tortoise.exceptions import DoesNotExist

from dex_screener.models import Asset
from dex_screener.models import SwapEvent
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.types.hydradx.substrate_events.xyk_buy_executed import XYKBuyExecutedPayload
from dex_screener.types.hydradx.substrate_events.xyk_sell_executed import XYKSellExecutedPayload


async def on_swap_executed(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKBuyExecutedPayload | XYKSellExecutedPayload],
) -> None:
    try:
        asset_in = await Asset.get(id=event.payload['asset_in'])
        assert asset_in.decimals is not None
        asset_out = await Asset.get(id=event.payload['asset_out'])
        assert asset_out.decimals is not None
        match event:
            case SubstrateEvent(
                name='XYK.BuyExecuted',
                payload={
                    'buy_price': int(minor_amount_in),
                    'amount': int(minor_amount_out),
                }
            ):
                direction = False

            case SubstrateEvent(
                name='XYK.SellExecuted',
                payload={
                    'sale_price': int(minor_amount_out),
                    'amount': int(minor_amount_in),
                }
            ):
                direction = True

            case _:
                return

        asset_amount_in = asset_in.from_minor(minor_amount_in)
        asset_amount_out = asset_out.from_minor(minor_amount_out)

        if asset_in.id < asset_out.id:
            swap_data = {
                'amount_0_in': asset_amount_in,
                'amount_1_out': asset_amount_out,
                'price': asset_amount_out / asset_amount_in,
            }
        else:
            swap_data = {
                'amount_0_out': asset_amount_out,
                'amount_1_in': asset_amount_in,
                'price': asset_amount_in / asset_amount_out,
            }

        swap_data.update(
            {
                'direction': direction,
                'maker': event.payload['who'],
                'pair_id': event.payload['pool'],
                'event_type': 'swap',
            }
        )
    except (DoesNotExist, AssertionError):
        return

    event_info = DexScreenerEventInfoDTO.from_event(event)

    swap = await SwapEvent.create(
        **event_info.model_dump(),
        **swap_data,
    )

    await event_info.update_latest_block()
