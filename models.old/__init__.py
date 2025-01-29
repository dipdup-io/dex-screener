import logging
import time
from enum import Enum
from functools import partial
from typing import Any

from dipdup import fields
from dipdup.models import Meta
from dipdup.models import Model

# NOTE: Asset amounts are stored in u128 which is up to 39 digits
U128DecimalField = partial(
    fields.DecimalField,
    max_digits=40,
    decimal_places=0,
)

# interface Block {
#   blockNumber: number;
#   blockTimestamp: number;
#   metadata?: Record<string, string>;
# }

# {
#   "block": {
#     "blockNumber": 100,
#     "blockTimestamp": 1698126147
#   }
# }


class Block(Model):
    block_number = fields.IntField(primary_key=True)
    block_timestamp = fields.IntField(null=True)
    written_timestamp = fields.IntField(null=True)
    metadata = fields.JSONField(null=True)


# interface Asset {
#   id: string;
#   name: string;
#   symbol: string;
#   totalSupply?: string | number;
#   circulatingSupply?: string | number;
#   coinGeckoId?: string;
#   coinMarketCapId?: string;
#   metadata?: Record<string, string>;
# }

# {
#   "asset": {
#     "id": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
#     "name": "Wrapped Ether",
#     "symbol": "WETH",
#     "totalSupply": 10000000,
#     "circulatingSupply": 900000,
#     "coinGeckoId": "ether",
#     "coinMarketCapId": "ether"
#   }
# }


class Asset(Model):
    id = fields.IntField(primary_key=True)
    name = fields.TextField()
    symbol = fields.TextField()
    total_supply = fields.IntField(null=True)
    circulating_supply = fields.IntField(null=True)
    coin_gecko_id = fields.TextField(null=True)
    coin_market_cap_id = fields.TextField(null=True)
    metadata = fields.JSONField(null=True)

    def get_repr(self) -> str:
        return f'`{self.name}` ({self.id} | {self.symbol})'


# interface Pair {
#   id: string;
#   dexKey: string;
#   asset0Id: string;
#   asset1Id: string;
#   createdAtBlockNumber?: number;
#   createdAtBlockTimestamp?: number;
#   createdAtTxnId?: string;
#   creator?: string;
#   feeBps?: number;
#   pool?: {
#     id: string;
#     name: string;
#     assetIds: string[];
#     pairIds: string[];
#     metadata?: Record<string, string>;
#   };
#   metadata?: Record<string, string>;
# }

# {
#   "pair": {
#     "id": "0x11b815efB8f581194ae79006d24E0d814B7697F6",
#     "dexKey": "uniswap",
#     "asset0Id": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
#     "asset1Id": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
#     "createdAtBlockNumber": 100,
#     "createdAtBlockTimestamp": 1698126147,
#     "createdAtTxnId": "0xe9e91f1ee4b56c0df2e9f06c2b8c27c6076195a88a7b8537ba8313d80e6f124e",
#     "feeBps": 100
#   }
# }


class Pair(Model):
    # FIXME: int or 0x?
    id = fields.TextField(primary_key=True)
    dex_key = fields.TextField()
    asset_0_id = fields.IntField()
    asset_1_id = fields.IntField()
    created_at_block_number = fields.IntField(null=True)
    created_at_block_timestamp = fields.IntField(null=True)
    created_at_txn_id = fields.TextField(null=True)
    creator = fields.TextField(null=True)
    fee_bps = fields.IntField(null=True)
    metadata = fields.JSONField(null=True)


# FIXME: int or 0x?
def get_pair_id(asset_0_id: int, asset_1_id: int) -> str:
    return f'{asset_0_id}_{asset_1_id}'


# interface SwapEvent {
#   eventType: "swap";
#   txnId: string;
#   txnIndex: number;
#   eventIndex: number;
#   maker: string;
#   pairId: string;
#   asset0In?: number | string;
#   asset1In?: number | string;
#   asset0Out?: number | string;
#   asset1Out?: number | string;
#   priceNative: number | string;
#   reserves?: {
#     asset0: number | string;
#     asset1: number | string;
#   };
#   metadata?: Record<string, string>;
# }
#
# interface JoinExitEvent {
#   eventType: "join" | "exit";
#   txnId: string;
#   txnIndex: number;
#   eventIndex: number;
#   maker: string;
#   pairId: string;
#   amount0: number | string;
#   amount1: number | string;
#   reserves?: {
#     asset0: number | string;
#     asset1: number | string;
#   };
#   metadata?: Record<string, string>;
# }


# TODO: Composite PKs in `sql/on_reindex`


class EventType(Enum):
    swap = 'swap'
    join = 'join'
    exit = 'exit'


class Event(Model):
    # NOTE: Composite PK; see `sql/on_reindex`
    event_type = fields.EnumField(EventType)
    composite_pk = fields.TextField(primary_key=True)
    # TODO: often duplicate of `composite_pk`
    txn_id = fields.TextField()
    txn_index = fields.IntField()
    event_index = fields.IntField()

    maker = fields.TextField()
    pair_id = fields.TextField()
    # swap
    asset_0_in = U128DecimalField(null=True)
    asset_1_in = U128DecimalField(null=True)
    asset_0_out = U128DecimalField(null=True)
    asset_1_out = U128DecimalField(null=True)
    # join/exit
    amount_0 = U128DecimalField(null=True)
    amount_1 = U128DecimalField(null=True)

    # TODO: Not implemented; change to DecimalField with higher precision
    # NOTE: Not defined for Join/Exit events, probably should be filtered out in API response
    price_native = U128DecimalField()
    reserves_asset_0 = U128DecimalField(null=True)
    reserves_asset_1 = U128DecimalField(null=True)


class OmnipoolPositions(Model):
    position_id = fields.IntField(primary_key=True)
    owner = fields.TextField()
    asset = fields.IntField()
    amount = U128DecimalField()
    shares = U128DecimalField()
    price = U128DecimalField()


class OTCOrders(Model):
    order_id = fields.IntField(primary_key=True)
    asset_in = fields.IntField()
    asset_out = fields.IntField()
    amount_in = U128DecimalField()
    amount_out = U128DecimalField()
    partially_fillable = fields.BooleanField()
    reversed = fields.BooleanField()


class Pool(Model):
    id = fields.TextField(primary_key=True)
    who = fields.TextField()
    asset_a = fields.IntField()
    asset_b = fields.IntField()
    initial_shares_amount = fields.IntField()
    share_token = fields.IntField()


_logger = logging.getLogger(__name__)


async def save_unprocesssed_payload(payload, note) -> None:
    try:
        await Meta.create(
            key=f'unprocessed_payload_{time.time()}',
            value={
                'payload': payload,
                'note': note,
            },
        )
    except TypeError as e:
        _logger.warning('payload is too big')


# NOTE: DOT for AssetHub, HDX for Hydration
NATIVE_ASSET_ID = -1


def extract_assets(path: list) -> tuple[int, ...] | None:
    asset_ids = []
    for item in path:
        if item['interior'] == 'Here':
            asset_id = NATIVE_ASSET_ID
        else:
            try:
                asset_id = item['interior']['X2'][-1]['GeneralIndex']
            except (KeyError, TypeError):
                _logger.warning('not a X2 path: %s', item)
                return None
        asset_ids.append(asset_id)

    if len(asset_ids) != 2:
        _logger.error('too many path elements: %s', asset_ids)
        return None

    return tuple(asset_ids)


def get_pool_id(payload: Any) -> str | None:

    assets = extract_assets(payload['pool_id'])
    if assets is None:
        _logger.warning('Failed to extract assets from pool_id %s', payload['pool_id'])
        return None

    return f'{assets[0]}_{assets[1]}'
