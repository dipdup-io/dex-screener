from dipdup.models.substrate import SubstrateEvent

from dex_screener.handlers.hydradx.asset.asset_type.abstract_hydration_asset import BaseHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType
from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError
from dex_screener.models import Asset


class HydrationExternalAsset(BaseHydrationAsset):
    asset_type: str = HydrationAssetType.External

    @classmethod
    async def handle_register_asset(cls, event: SubstrateEvent) -> Asset:
        match event.data.args:
            case {'assetId': int(asset_id)}:
                pass
            case _:
                raise InvalidEventDataError('Unhandled Event Data.')

        return await cls.update_asset(
            asset_id=asset_id,
            updated_fields={},
            event=event,
        )
