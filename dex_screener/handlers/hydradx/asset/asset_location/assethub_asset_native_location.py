from typing import Any

from dex_screener.handlers.hydradx.asset.asset_location.abstract_asset_native_location import AbstractAssetNativeLocation
from dex_screener.handlers.hydradx.asset.asset_location.dto import ExternalMetadataDTO


class AssetHubAssetNativeLocation(AbstractAssetNativeLocation):
    def _prepare_parachain_query_parameters(self, interior_value: dict) -> list:
        match interior_value:
            case [
                *_,
                {'__kind': 'GeneralIndex', 'value': int(external_id)|str(external_id)}
            ]:
                pass
            case [
                {'__kind': 'Parachain', 'value': self.parachain_id},
                {'__kind': 'Parachain', 'value': int()},
                {'__kind': 'Parachain', 'value': int(external_id)}
            ]:
                pass
            case _:
                raise ValueError('Unhandled interior value: %s.', interior_value)

        return [external_id]

    async def _request_parachain_query(self, params: list) -> Any:
        return await self._client.query('Assets', 'Metadata', params)

    def _extract_asset_metadata_from_response(self, response: Any) -> ExternalMetadataDTO:
        return ExternalMetadataDTO(
            name=response.value['name'],
            symbol=response.value['symbol'],
            decimals=response.value['decimals'],
        )
