from dipdup.models.substrate import SubstrateEvent

from dex_screener.handlers.hydradx.asset.asset_type import DipDupEventDataCollectPayloadUnhandledError
from dex_screener.handlers.hydradx.asset.asset_type import validate_framework_exception
from dex_screener.handlers.hydradx.asset.asset_type.abstract_hydration_asset import BaseHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType
from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError
from dex_screener.models import Asset


class HydrationTokenAsset(BaseHydrationAsset):
    asset_type: str = HydrationAssetType.Token

    @classmethod
    async def handle_register_asset(cls, event: SubstrateEvent) -> Asset:
        try:
            return await super(cls, cls).handle_register_asset(event)
        except DipDupEventDataCollectPayloadUnhandledError as exception:
            validate_framework_exception(exception)

        match event.data.args:
            case {
                'assetId': int(asset_id),
                'assetName': str(asset_name_hex),
                'symbol': str(asset_symbol_hex),
                'decimals': int(asset_decimals),
            }:
                asset_name = bytes.fromhex(asset_name_hex.removeprefix('0x')).decode()
                asset_symbol = bytes.fromhex(asset_symbol_hex.removeprefix('0x')).decode()
            case _:
                raise InvalidEventDataError('Unhandled Event Data.')

        return await cls.create_asset(
            asset_id=asset_id,
            event=event,
            fields={
                'name': asset_name,
                'symbol': asset_symbol,
                'decimals': asset_decimals,
            },
        )

    @classmethod
    async def handle_update_asset(cls, event: SubstrateEvent) -> Asset:
        try:
            return await super().handle_update_asset(event)
        except DipDupEventDataCollectPayloadUnhandledError as exception:
            validate_framework_exception(exception)

        match event.data.args:
            case {
                'assetId': int(asset_id),
                'assetName': str(asset_name_hex),
                'symbol': str(asset_symbol_hex),
                'decimals': int(asset_decimals),
            }:
                asset_name = bytes.fromhex(asset_name_hex.removeprefix('0x')).decode()
                asset_symbol = bytes.fromhex(asset_symbol_hex.removeprefix('0x')).decode()
                updated_fields = {
                    'name': asset_name,
                    'symbol': asset_symbol,
                    'decimals': asset_decimals,
                }
            case {
                'assetId': int(asset_id),
                'assetName': str(asset_name_hex),
            }:
                asset_name = bytes.fromhex(asset_name_hex.removeprefix('0x')).decode()
                updated_fields = {
                    'name': asset_name,
                }
            case _:
                raise InvalidEventDataError('Unhandled Event Data.')

        return await cls.update_asset(
            asset_id=asset_id,
            updated_fields=updated_fields,
            event=event,
        )
