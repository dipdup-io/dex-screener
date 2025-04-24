from typing import Any

from dex_screener.handlers.hydradx.asset.asset_location.abstract_asset_native_location import (
    AbstractAssetNativeLocation,
)
from dex_screener.handlers.hydradx.asset.asset_location.dto import ExternalMetadataDTO
from dex_screener.handlers.hydradx.asset.asset_location.types import GeneralKey
from dex_screener.handlers.hydradx.asset.asset_location.types import Interior
from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError


class PendulumAssetNativeLocation(AbstractAssetNativeLocation):
    parachain_id: int = 2094
    node_url: str = 'wss://rpc-pendulum.prd.pendulumchain.tech'

    def _prepare_parachain_query_parameters(self, interior: Interior) -> list:
        match interior:
            case [
                *_,
                GeneralKey(asset_code),
                GeneralKey(issuer),
            ]:
                return [{'Stellar': {'AlphaNum4': {'code': str(asset_code), 'issuer': str(issuer)}}}]

        raise InvalidEventDataError(f'Unhandled interior value: {interior}.')

    async def _request_parachain_query(self, params: list) -> Any:
        return await self._client.query('AssetRegistry', 'Metadata', params)

    def _extract_asset_metadata_from_response(self, response: Any) -> ExternalMetadataDTO:
        return ExternalMetadataDTO(
            name=response.value['name'],
            symbol=response.value['symbol'],
            decimals=response.value['decimals'],
        )
