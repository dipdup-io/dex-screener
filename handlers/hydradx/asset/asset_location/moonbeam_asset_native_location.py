from typing import Any

from dex_screener.handlers.hydradx.asset.asset_location.abstract_asset_native_location import (
    AbstractAssetNativeLocation,
)
from dex_screener.handlers.hydradx.asset.asset_location.dto import ExternalMetadataDTO
from dex_screener.handlers.hydradx.asset.asset_location.types import AccountKey20
from dex_screener.handlers.hydradx.asset.asset_location.types import Interior
from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError


class MoonbeamAssetNativeLocation(AbstractAssetNativeLocation):
    parachain_id: int = 2004
    node_datasource: str = 'asset_moonbeam'

    def _prepare_parachain_query_parameters(self, interior: Interior) -> list:
        match interior:
            case [*_, AccountKey20(external_id)]:
                pass
            case _:
                raise InvalidEventDataError(f'Unhandled interior value: {interior}.')

        return [external_id]

    async def _request_parachain_query(self, params: list) -> Any:
        return await self._client.query('Assets', 'Metadata', params)

    def _extract_asset_metadata_from_response(self, response: Any) -> ExternalMetadataDTO:
        return ExternalMetadataDTO(
            name=response.value['name'],
            symbol=response.value['symbol'],
            decimals=response.value['decimals'],
        )
