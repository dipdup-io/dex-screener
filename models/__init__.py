from enum import Enum
from functools import partial

from dipdup import fields
from dipdup.models import Model

# NOTE: Asset amounts are stored in u128 which is up to 39 digits
U128DecimalField = partial(
    fields.DecimalField,
    max_digits=40,
    decimal_places=40,
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
    block_timestamp = fields.IntField()
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
    id = fields.IntField(primary_key=True)
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
    price_native = fields.IntField()
    reserves_asset_0 = U128DecimalField(null=True)
    reserves_asset_1 = U128DecimalField(null=True)


class Pool(Model):
    id = fields.TextField(primary_key=True)
    who = fields.TextField()
    asset_a = fields.IntField()
    asset_b = fields.IntField()
    initial_shares_amount = fields.IntField()
    share_token = fields.IntField()



def fix_multilocation(data):
    if isinstance(data, list):
        return tuple(fix_multilocation(item) for item in data)

    if isinstance(data, dict):
        if 'interior' in data:
            # Handle interior dictionary
            result = {'parents': data['parents']}
            interior = data['interior']

            if '__kind' in interior:
                kind = interior['__kind']
                if 'value' in interior:
                    value = interior['value']
                    if isinstance(value, list):
                        # Handle list of values (like in X2 case)
                        value = tuple(
                            {item['__kind']: int(item['value']) if isinstance(item['value'], str) else item['value']}
                            for item in value
                        )
                    elif isinstance(value, str):
                        value = int(value)
                    result['interior'] = {kind: value}
                else:
                    result['interior'] = kind
            else:
                result['interior'] = fix_multilocation(interior)
            return result

        # Process other dictionaries
        return {key: fix_multilocation(value) for key, value in data.items()}

    # Return primitive values as-is
    return data
