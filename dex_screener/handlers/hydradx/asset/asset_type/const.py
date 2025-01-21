from dex_screener.handlers.hydradx.asset.asset_type import AbstractHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType as AssetType
from dex_screener.handlers.hydradx.asset.asset_type.hydration_external_asset import HydrationExternalAsset
from dex_screener.handlers.hydradx.asset.asset_type.hydration_stable_swap_asset import HydrationStableSwapAsset
from dex_screener.handlers.hydradx.asset.asset_type.hydration_token_asset import HydrationTokenAsset

REQUIRED_ASSET_TYPE_MAP: dict[str, type[AbstractHydrationAsset]] = {
    AssetType.Token: HydrationTokenAsset,
    AssetType.External: HydrationExternalAsset,
    AssetType.StableSwap: HydrationStableSwapAsset,
}
UNUSED_ASSET_TYPE_LIST: list[str] = [
    AssetType.Bond,
    AssetType.PoolShare,
    AssetType.XYK,
]
