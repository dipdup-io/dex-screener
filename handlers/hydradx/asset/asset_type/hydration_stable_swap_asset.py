from dipdup.models.substrate import SubstrateEvent

from dex_screener.handlers.hydradx.asset.asset_type import DipDupEventDataCollectPayloadUnhandledError
from dex_screener.handlers.hydradx.asset.asset_type import validate_framework_exception
from dex_screener.handlers.hydradx.asset.asset_type.abstract_hydration_asset import BaseHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType
from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError
from dex_screener.models import Asset


class HydrationStableSwapAsset(BaseHydrationAsset):
    asset_type: str = HydrationAssetType.StableSwap

    @classmethod
    async def handle_register_asset(cls, event: SubstrateEvent) -> Asset:
        try:
            return await super(cls, cls).handle_register_asset(event)
        except DipDupEventDataCollectPayloadUnhandledError as exception:
            validate_framework_exception(exception)

        match event.payload:
            case {
                'asset_id': int(asset_id),
                'asset_name': str(asset_name_hex),
                'symbol': str(asset_symbol_hex),
                'decimals': int(asset_decimals),
            }:
                asset_name = bytes.fromhex(asset_name_hex.removeprefix('0x')).decode()
                asset_symbol = bytes.fromhex(asset_symbol_hex.removeprefix('0x')).decode()
            case _:
                raise InvalidEventDataError(f'Unhandled Event Data: {event.data}.')

        return await cls.create_asset(
            asset_id=asset_id,
            event=event,
            fields={
                'name': asset_name,
                'symbol': asset_symbol,
                'decimals': asset_decimals,
            },
        )
