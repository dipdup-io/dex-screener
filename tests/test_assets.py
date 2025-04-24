from __future__ import annotations

import pytest

from dex_screener.handlers.hydradx.asset.asset_count.asset_price import AssetPrice
from dex_screener.handlers.hydradx.asset.asset_count.market_pair import MarketPair
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType
from dex_screener.models import Asset

Asset.updated_at_block_id = None

DOT = Asset(
    id=5,
    name='Polkadot',
    symbol='DOT',
    decimals=10,
    asset_type=HydrationAssetType.Token,
)
HDX = Asset(
    id=0,
    name='HydraDX',
    symbol='HDX',
    decimals=10,
    asset_type=HydrationAssetType.Token,
)
USDt = Asset(
    id=10,
    name='USDT (Polkadot Asset Hub)',
    symbol='USDt',
    decimals=6,
    asset_type=HydrationAssetType.Token,
)

UNQ = Asset(
    id=25,
    name='Unique network',
    symbol='UNQ',
    decimals=18,
    asset_type=HydrationAssetType.Token,
)


class TestAssets:
    def test_asset_amount(self):
        dot_amount = DOT.from_minor('59774308173160')
        assert dot_amount == DOT.amount('5977.43081731600001')
        assert dot_amount.minor == 59774308173160
        assert dot_amount.minor == DOT.to_minor(dot_amount)
        assert dot_amount.asset is DOT
        assert str(dot_amount) == '5977.430817316'
        assert repr(dot_amount) == 'DOT(5977.430817316)'
        assert dot_amount.asset.symbol == 'DOT'

        with pytest.raises(TypeError, match='Cannot divide int by DOT'):
            1 / dot_amount

        assert dot_amount / '1.0' == dot_amount

        assert USDt.amount('614') / DOT.amount('100') == AssetPrice('6.14', MarketPair(DOT, USDt))
        assert USDt.amount('778') / DOT.amount('3') == AssetPrice(
            '259.33333333333333333333333333333333333333333333333333', MarketPair(DOT, USDt)
        )

        assert dot_amount / dot_amount == 1
