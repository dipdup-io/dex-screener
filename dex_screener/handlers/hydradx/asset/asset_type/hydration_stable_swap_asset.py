from dex_screener.handlers.hydradx.asset.asset_type.abstract_hydration_asset import BaseHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType


class HydrationStableSwapAsset(BaseHydrationAsset):
    asset_type: str = HydrationAssetType.StableSwap
