from aiosubstrate import SubstrateInterface

from dex_screener.handlers.hydradx.asset.asset_location.abstract_asset_native_location import AbstractAssetNativeLocation
from dex_screener.handlers.hydradx.asset.asset_location.assethub_asset_native_location import AssetHubAssetNativeLocation
from dex_screener.handlers.hydradx.asset.asset_location.pendulum_asset_native_location import PendulumAssetNativeLocation
from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError

ASSET_LOCATION_CLASS_LIST = [
    AssetHubAssetNativeLocation,
    PendulumAssetNativeLocation,
]

ASSET_LOCATION_CLASS_MAP: dict[int, type(AbstractAssetNativeLocation)] = {
    asset_location_class.parachain_id: asset_location_class for asset_location_class in ASSET_LOCATION_CLASS_LIST
}

ASSET_LOCATION_MAP: dict[int, AbstractAssetNativeLocation] = {}


def get_asset_location(parachain_id: int):
    if parachain_id not in ASSET_LOCATION_CLASS_MAP:
        raise InvalidEventDataError(f'Unsupported `parachain_id`: {parachain_id}.')
    if parachain_id not in ASSET_LOCATION_MAP:
        asset_location_class = ASSET_LOCATION_CLASS_MAP[parachain_id]
        parachain_client = SubstrateInterface(asset_location_class.node_url)
        asset_location = asset_location_class(client=parachain_client)
        ASSET_LOCATION_MAP[parachain_id] = asset_location
    else:
        asset_location = ASSET_LOCATION_MAP[parachain_id]

    return asset_location
