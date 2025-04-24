from dex_screener.handlers.hydradx.asset.asset_type.abstract_hydration_asset import HexNamedHydrationAsset
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType


class HydrationBondAsset(HexNamedHydrationAsset):
    asset_type: str = HydrationAssetType.Bond

    @classmethod
    def _get_base_asset_id(cls, asset_name_hex_prefixed: str) -> int:
        return int.from_bytes(bytes.fromhex(asset_name_hex_prefixed[2:10]), 'little', signed=False)
