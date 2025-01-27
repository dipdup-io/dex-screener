from dex_screener.handlers.hydradx.asset.asset_type import HexNamedHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType


class HydrationBondAsset(HexNamedHydrationAsset):
    asset_type: str = HydrationAssetType.Bond
