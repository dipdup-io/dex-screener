import logging
import time
from enum import Enum
from enum import StrEnum
from functools import partial
from typing import Any

from dipdup import fields
from dipdup.models import Meta
from dipdup.models import Model
from dipdup.runtimes import extract_multilocation_payload
from dipdup.models.substrate import SubstrateEventData
from tortoise import ForeignKeyFieldInstance


# from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType


class HydrationAssetType(StrEnum):
    Token = 'Token'
    External = 'External'
    StableSwap = 'StableSwap'
    Bond = 'Bond'
    PoolShare = 'PoolShare'
    XYK = 'XYK'
    ERC20 = 'Erc20'


class DexKey(StrEnum):
    assethub = 'assethub'
    hydradx_omnipool = 'hydradx_omnipool'
    hydradx_otc = 'hydradx_otc'
    hydradx_stableswap = 'hydradx_stableswap'
    hydradx_xyk = 'hydradx_xyk'


class Block(Model):
    class Meta:
        table = 'dex_block'
        model = 'models.Block'

    block_number = fields.IntField(primary_key=True)
    block_timestamp = fields.IntField(null=True)
    written_timestamp = fields.IntField(null=True)
    metadata = fields.JSONField(null=True)


class Asset(Model):
    class Meta:
        table = 'dex_asset'
        model = 'models.Asset'

    id = fields.IntField(primary_key=True)
    name = fields.TextField(null=True)
    symbol = fields.TextField(null=True)
    total_supply = fields.IntField(null=True)
    circulating_supply = fields.IntField(null=True)
    coin_gecko_id = fields.TextField(null=True)
    coin_market_cap_id = fields.TextField(null=True)
    metadata = fields.JSONField(null=True)

    decimals = fields.IntField(null=True)
    asset_type = fields.EnumField(enum_type=HydrationAssetType, db_index=True, null=True)
    # updated_at_block: ForeignKeyFieldInstance[Block] = fields.ForeignKeyField(
    #     model_name=Block.Meta.model,
    #     source_field='updated_at_block_id',
    #     to_field='level',
    # )

    def get_repr(self) -> str:
        return f'`{self.name}` ({self.id} | {self.symbol})'


class Pair(Model):
    id = fields.TextField(primary_key=True)
    dex_key = fields.EnumField(DexKey, db_index=True)
    asset_0_id = fields.IntField()
    asset_1_id = fields.IntField()
    created_at_block_number = fields.IntField(null=True)
    created_at_block_timestamp = fields.IntField(null=True)
    created_at_txn_id = fields.TextField(null=True)
    creator = fields.TextField(null=True)
    fee_bps = fields.IntField(null=True)
    metadata = fields.JSONField(null=True)

    class Meta:
        table = 'dex_pair'
        model = 'models.Pair'
        unique_together = ('dex_key', 'asset_0_id', 'asset_1_id')


class SwapEvent(Model):
    class Meta:
        table = 'dex_swap_event'
        model = 'dex_screener.models.SwapEvent'

    # TODO: add dex id to final event model
    id = fields.IntField(primary_key=True)
    txn_id = fields.TextField()
    txn_index = fields.IntField(null=True)
    event_index = fields.IntField()
    maker = fields.TextField()
    pair: ForeignKeyFieldInstance[Pair] = fields.ForeignKeyField(
        model_name=Pair.Meta.model,
        source_field='pair_id',
        to_field='id',
    )
    asset_in_id = fields.IntField()
    asset_out_id = fields.IntField()
    amount_in = fields.DecimalField(max_digits=100, decimal_places=50, null=True)
    amount_out = fields.DecimalField(max_digits=100, decimal_places=50, null=True)
    direction = fields.BooleanField(description='0: Buy, 1: Sell')
    price = fields.DecimalField(max_digits=100, decimal_places=50, description='Always amount_out/amount_in')
    created_at_block: ForeignKeyFieldInstance[Block] = fields.ForeignKeyField(
        model_name=Block.Meta.model,
        source_field='created_at_block_number',
        to_field='block_number',
        null=True,
    )


# NOTE: Asset amounts are stored in u128 which is up to 39 digits
U128DecimalField = partial(
    fields.DecimalField,
    max_digits=40,
    decimal_places=0,
)


def get_pair_id(asset_0_id: int, asset_1_id: int) -> str:
    _min = min(asset_0_id, asset_1_id)
    _max = max(asset_0_id, asset_1_id)
    return f'{_min}_{_max}'



class EventType(Enum):
    swap = 'swap'
    join = 'join'
    exit = 'exit'


class Event(Model):
    event_type = fields.EnumField(EventType)
    composite_pk = fields.TextField(primary_key=True)
    # NOTE: in most cases duplicate of `composite_pk`
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
    price_native = fields.DecimalField(max_digits=100, decimal_places=50, description='Always amount_out/amount_in')
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
NATIVE_ASSET_ID = 0


def get_pool_assets(payload: Any) -> tuple[int, int]:
    path = payload['pool_id'] if 'pool_id' in payload else payload['path']
    loc = extract_multilocation_payload(path)

    if len(loc) != 2:
        raise NotImplementedError

    if loc[0][0]['interior'] == 'Here':
        asset_0, asset_1 = 0, loc[1][0]['interior'][1]['GeneralIndex']
    else:
        asset_0, asset_1 = loc[0][0]['interior'][1]['GeneralIndex'], 0

    return int(asset_0), int(asset_1)


def get_composite_key(data: SubstrateEventData) -> str:
    return f'{data.block_number}-{data.extrinsic_index or 0}-{data.index}'
