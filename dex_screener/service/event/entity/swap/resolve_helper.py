from dex_screener.service.event.entity.swap.dto import MarketDataArgsDTO
from dex_screener.service.event.entity.swap.exception import InvalidSwapEventMarketDataError


class ClassicPoolSwapEventMarketDataHelper:
    @classmethod
    async def extract_args_from_payload(cls, payload):
        match payload:
            case {
                'who': str(maker),
                'asset_in': int(asset_in_id),
                'asset_out': int(asset_out_id),
                'buy_price': int(minor_amount_in),
                'amount': int(minor_amount_out),
            }:
                pass
            case {
                'who': str(maker),
                'asset_in': int(asset_in_id),
                'asset_out': int(asset_out_id),
                'sale_price': int(minor_amount_out),
                'amount': int(minor_amount_in),
            }:
                pass
            case _:
                raise InvalidSwapEventMarketDataError(f'Unhandled Swap Event Payload: {payload}.')

        return MarketDataArgsDTO(
            maker=maker,
            asset_in_id=asset_in_id,
            asset_out_id=asset_out_id,
            minor_amount_in=minor_amount_in,
            minor_amount_out=minor_amount_out,
        )


class MultiAssetPoolSwapEventMarketDataHelper:
    @classmethod
    async def extract_args_from_payload(cls, payload):
        match payload:
            case {
                'who': str(maker),
                'asset_in': int(asset_in_id),
                'asset_out': int(asset_out_id),
                'amount_in': int(minor_amount_in),
                'amount_out': int(minor_amount_out),
            }:
                pass
            case _:
                raise InvalidSwapEventMarketDataError(f'Unhandled Swap Event Payload: {payload}.')

        return MarketDataArgsDTO(
            maker=maker,
            asset_in_id=asset_in_id,
            asset_out_id=asset_out_id,
            minor_amount_in=minor_amount_in,
            minor_amount_out=minor_amount_out,
        )
