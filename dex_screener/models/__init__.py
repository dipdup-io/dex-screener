from enum import StrEnum

from dipdup import fields
from dipdup.models import Model
from tortoise import ForeignKeyFieldInstance

from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType


class DexKey(StrEnum):
    hydradx: str = 'hydradx'


class Block(Model):
    class Meta:
        table = 'dex_block'
        model = 'models.Block'

    level = fields.IntField(primary_key=True)
    timestamp = fields.IntField()


class Asset(Model):
    class Meta:
        table = 'dex_asset'
        model = 'models.Asset'

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, unique=True, null=True)
    symbol = fields.CharField(max_length=16, null=True)
    decimals = fields.IntField(null=True)
    asset_type = fields.EnumField(enum_type=HydrationAssetType, db_index=True)
    updated_at_block: ForeignKeyFieldInstance[Block] = fields.ForeignKeyField(
        model_name=Block.Meta.model,
        source_field='updated_at_block_id',
        to_field='level',
    )


class Pair(Model):
    class Meta:
        table = 'dex_pair'
        model = 'models.Pair'
        unique_together = ('dex_key', 'asset_0_id', 'asset_1_id')

    id = fields.CharField(primary_key=True, max_length=66)
    dex_key = fields.EnumField(DexKey, db_index=True)
    asset_0: ForeignKeyFieldInstance[Asset] = fields.ForeignKeyField(
        model_name=Asset.Meta.model,
        source_field='asset_0_id',
        to_field='id',
        related_name='pair_asset_0',
    )
    asset_1: ForeignKeyFieldInstance[Asset] = fields.ForeignKeyField(
        model_name=Asset.Meta.model,
        source_field='asset_1_id',
        to_field='id',
        related_name='pair_asset_1',
    )

    created_at_block: ForeignKeyFieldInstance[Block] = fields.ForeignKeyField(
        model_name=Block.Meta.model,
        source_field='created_at_block_id',
        to_field='level',
    )
    created_at_txn_id = fields.CharField(max_length=66)
    fee_bps = fields.IntField(null=True)


class SwapEvent(Model):
    class Meta:
        table = 'dex_swap_event'
        model = 'dex_screener.models.SwapEvent'

    id = fields.IntField(primary_key=True)
    txn_id = fields.CharField(max_length=66)
    txn_index = fields.IntField(null=True)
    event_index = fields.IntField()
    maker = fields.CharField(max_length=66)
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
        source_field='created_at_block_id',
        to_field='level',
    )
