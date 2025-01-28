from typing import Any

from dex_screener.handlers.hydradx.asset.asset_location.abstract_asset_native_location import (
    AbstractAssetNativeLocation,
)
from dex_screener.handlers.hydradx.asset.asset_location.dto import ExternalMetadataDTO


class PendulumAssetNativeLocation(AbstractAssetNativeLocation):
    parachain_id: int = 2094
    node_url: str = 'wss://rpc-pendulum.prd.pendulumchain.tech'

    def _prepare_parachain_query_parameters(self, interior_value: dict) -> list:
        match interior_value:
            case [
                *_,
                {'__kind': 'GeneralKey', 'data': str(asset_code_data), 'length': int(asset_code_length)},
                {'__kind': 'GeneralKey', 'data': str(issuer_data), 'length': int(issuer_length)},
            ]:

                return [
                    {
                        'Stellar': {
                            'AlphaNum4': {
                                'code': asset_code_data[0 : 2 * (1 + asset_code_length)],
                                'issuer': issuer_data[0 : 2 * (1 + issuer_length)],
                            }
                        }
                    }
                ]

        raise ValueError('Unhandled interior value: %s.', interior_value)

    async def _request_parachain_query(self, params: list) -> Any:
        return await self._client.query('AssetRegistry', 'Metadata', params)

    def _extract_asset_metadata_from_response(self, response: Any) -> ExternalMetadataDTO:
        return ExternalMetadataDTO(
            name=response.value['name'],
            symbol=response.value['symbol'],
            decimals=response.value['decimals'],
        )
