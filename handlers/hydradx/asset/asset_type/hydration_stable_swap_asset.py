import logging

from dipdup.models.substrate import SubstrateEvent

from dex_screener.handlers.hydradx.asset.asset_type import DipDupEventDataCollectPayloadUnhandledError
from dex_screener.handlers.hydradx.asset.asset_type.abstract_hydration_asset import BaseHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType
from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError
from dex_screener.models import Asset

_logger = logging.getLogger(__name__)


class HydrationStableSwapAsset(BaseHydrationAsset):
    asset_type: str = HydrationAssetType.StableSwap

    @classmethod
    async def handle_register_asset(cls, event: SubstrateEvent) -> Asset:
        try:
            return await super(cls, cls).handle_register_asset(event)
        except DipDupEventDataCollectPayloadUnhandledError as exception:
            _logger.warning(
                'Unhandled DipDup Event Data: %s. Event: %s',
                exception,
                event,
            )

        match event.payload:
            case {
                'asset_id': int(asset_id),
                'asset_name': str(asset_name),
                'symbol': str(asset_symbol),
                'decimals': int(asset_decimals),
            }:
                pass
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
