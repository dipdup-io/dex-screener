from dex_screener.handlers.hydradx.asset.asset_type.abstract_hydration_asset import AbstractHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType as AssetType
from dex_screener.handlers.hydradx.asset.asset_type.hydration_bond_asset import HydrationBondAsset
from dex_screener.handlers.hydradx.asset.asset_type.hydration_erc20_asset import HydrationERC20Asset
from dex_screener.handlers.hydradx.asset.asset_type.hydration_external_asset import HydrationExternalAsset
from dex_screener.handlers.hydradx.asset.asset_type.hydration_pool_share_asset import HydrationPoolShareAsset
from dex_screener.handlers.hydradx.asset.asset_type.hydration_stable_swap_asset import HydrationStableSwapAsset
from dex_screener.handlers.hydradx.asset.asset_type.hydration_token_asset import HydrationTokenAsset
from dex_screener.handlers.hydradx.asset.asset_type.hydration_xyk_asset import HydrationXYKAsset

ASSET_TYPE_MAP: dict[str, type[AbstractHydrationAsset]] = {
    AssetType.Token: HydrationTokenAsset,
    AssetType.External: HydrationExternalAsset,
    AssetType.StableSwap: HydrationStableSwapAsset,
    AssetType.Bond: HydrationBondAsset,
    AssetType.PoolShare: HydrationPoolShareAsset,
    AssetType.ERC20: HydrationERC20Asset,
    AssetType.XYK: HydrationXYKAsset,
}
