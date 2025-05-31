from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from aiosubstrate import SubstrateInterface
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.handlers.hydradx.asset.asset_location.dto import ExternalMetadataDTO
    from dex_screener.handlers.hydradx.asset.asset_location.types import Interior
    from dex_screener.models import Asset
from dex_screener.handlers.hydradx.asset.asset_type.hydration_external_asset import HydrationExternalAsset


class AbstractAssetNativeLocation(ABC):
    parachain_id: int = NotImplemented
    node_datasource: str = NotImplemented

    def __init__(self, client: SubstrateInterface):
        self._client: SubstrateInterface = client

    @abstractmethod
    def _prepare_parachain_query_parameters(self, interior: Interior) -> list:
        raise NotImplementedError

    @abstractmethod
    async def _request_parachain_query(self, params: list) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _extract_asset_metadata_from_response(self, response: Any) -> ExternalMetadataDTO:
        raise NotImplementedError

    @staticmethod
    async def _update_asset_metadata(
        asset_id: int, asset_metadata: ExternalMetadataDTO, event: SubstrateEvent
    ) -> Asset:
        return await HydrationExternalAsset.update_asset(asset_id, asset_metadata.model_dump(), event)

    async def update_asset_with_external_metadata(self, asset_id, interior: Interior, event: SubstrateEvent) -> Asset:
        params = self._prepare_parachain_query_parameters(interior)
        response = await self._request_parachain_query(params)
        asset_metadata: ExternalMetadataDTO = self._extract_asset_metadata_from_response(response)
        asset: Asset = await self._update_asset_metadata(asset_id, asset_metadata, event)

        return asset
