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

        asset_id, fields = cls._match_event_payload(event.payload)

        return await cls.create_asset(
            asset_id=asset_id,
            event=event,
            fields=fields,
        )

    @classmethod
    async def handle_update_asset(cls, event: SubstrateEvent) -> Asset:
        try:
            return await super().handle_update_asset(event)
        except DipDupEventDataCollectPayloadUnhandledError as exception:
            validate_framework_exception(exception)

        asset_id, fields = cls._match_event_payload(event.payload)

        return await cls.update_asset(
            asset_id=asset_id,
            updated_fields=fields,
            event=event,
        )

    @classmethod
    def _match_event_payload(cls, payload) -> tuple[int, dict[str, int | str]]:
        match payload:
            case {
                'asset_id': int(asset_id),
                **event_items,
            }:
                fields: dict[str, str | int] = {}
                for key, value in event_items.items():
                    match key, value:
                        case 'asset_name', str(asset_name_hex):
                            asset_name = bytes.fromhex(asset_name_hex.removeprefix('0x')).decode()
                            fields.update({'name': asset_name})
                        case 'symbol', str(asset_symbol_hex):
                            asset_symbol = bytes.fromhex(asset_symbol_hex.removeprefix('0x')).decode()
                            fields.update({'symbol': asset_symbol})
                        case 'decimals', int(asset_decimals):
                            fields.update({'decimals': asset_decimals})
                        case 'asset_type' | 'existential_deposit' | 'is_sufficient', _:
                            pass
                        case _:
                            raise InvalidEventDataError(f'Unhandled Event Data: {event_items}.')

            case _:
                raise InvalidEventDataError(f'Unhandled Event Data: {payload}.')

        return asset_id, fields
