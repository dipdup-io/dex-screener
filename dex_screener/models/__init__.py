from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from dipdup import fields
from dipdup.fields import ForeignKeyField
from dipdup.fields import ManyToManyField
from dipdup.fields import OneToOneField
from dipdup.models import Model

if TYPE_CHECKING:
    from tortoise.fields.relational import ForeignKeyFieldInstance
    from tortoise.fields.relational import ManyToManyFieldInstance
    from tortoise.fields.relational import OneToOneFieldInstance

    from dex_screener.handlers.hydradx.asset.asset_amount.types import AnyTypeAmount

from dex_screener.handlers.hydradx.asset.asset_amount import AssetAmount
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType
from dex_screener.models.dex_fields import AccountField as AccountField
from dex_screener.models.enum import DexKey as DexKey


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
    name = fields.CharField(max_length=255, null=True)
    symbol = fields.CharField(max_length=16, null=True)
    decimals = fields.IntField(null=True)
    asset_type = fields.EnumField(enum_type=HydrationAssetType, db_index=True)

    updated_at_block: ForeignKeyFieldInstance[Block] = ForeignKeyField(
        model_name=Block.Meta.model,
        source_field='updated_at_block_id',
        to_field='level',
    )

    def amount(self, amount: AnyTypeAmount) -> AssetAmount:
        amount = Decimal(amount).quantize(Decimal('1.' + '0' * self.decimals))
        return AssetAmount(asset=self, amount=amount)

    def from_minor(self, minor_amount: AnyTypeAmount) -> AssetAmount:
        amount = Decimal(int(minor_amount)) / 10**self.decimals
        return self.amount(amount=amount)


class Pool(Model):
    class Meta:
        table = 'dex_pool'
        model = 'models.Pool'

    id = fields.TextField(primary_key=True)
    account = AccountField(null=True)
    dex_key = fields.EnumField(enum_type=DexKey, db_index=True)
    assets: ManyToManyFieldInstance[Asset] = ManyToManyField(
        model_name=Asset.Meta.model,
        # through='models.AssetPoolReserve',
        through='dex_asset_pool_reserve',
        forward_key='asset_id',
        backward_key='pool_id',
        related_name='pools',
    )
    lp_token: OneToOneFieldInstance[Asset] = OneToOneField(
        model_name=Asset.Meta.model,
        related_name='liquidity_pool',
        to_field='id',
        source_field='lp_token_id',
        null=True,
    )


class AssetPoolReserve(Model):
    class Meta:
        table = 'dex_asset_pool_reserve'
        model = 'models.AssetPoolReserve'
        unique_together = ('pool', 'asset')

    id = fields.IntField(primary_key=True)
    asset: ForeignKeyFieldInstance[Asset] = ForeignKeyField(
        model_name=Asset.Meta.model,
        source_field='asset_id',
        to_field='id',
        related_name='reserve',
    )
    pool: ForeignKeyFieldInstance[Pool] = ForeignKeyField(
        model_name=Pool.Meta.model,
        source_field='pool_id',
        to_field='id',
        related_name='reserves',
    )
    reserve = fields.CharField(max_length=40, null=True)


class Pair(Model):
    class Meta:
        table = 'dex_pair'
        model = 'models.Pair'
        unique_together = ('pool', 'asset_0', 'asset_1')

    id = fields.CharField(primary_key=True, max_length=66)
    dex_key = fields.EnumField(DexKey, db_index=True)
    asset_0: ForeignKeyFieldInstance[Asset] = ForeignKeyField(
        model_name=Asset.Meta.model,
        source_field='asset_0_id',
        to_field='id',
        related_name='pair_asset_0',
    )
    asset_1: ForeignKeyFieldInstance[Asset] = ForeignKeyField(
        model_name=Asset.Meta.model,
        source_field='asset_1_id',
        to_field='id',
        related_name='pair_asset_1',
    )
    pool: ForeignKeyFieldInstance[Pool] = ForeignKeyField(
        model_name=Pool.Meta.model,
        source_field='pool_id',
        to_field='id',
    )

    created_at_block: ForeignKeyFieldInstance[Block] = ForeignKeyField(
        model_name=Block.Meta.model,
        source_field='created_at_block_id',
        to_field='level',
    )
    created_at_txn_id = fields.CharField(max_length=66)
    fee_bps = fields.IntField(null=True)


class SwapEvent(Model):
    class Meta:
        table = 'dex_swap_event'
        model = 'models.SwapEvent'

    id = fields.IntField(primary_key=True)
    timestamp = fields.DatetimeField()
    txn_id = fields.CharField(max_length=66)
    txn_index = fields.IntField(null=True)
    event_index = fields.IntField()
    maker = AccountField()
    pair: ForeignKeyFieldInstance[Pair] = ForeignKeyField(
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
    created_at_block: ForeignKeyFieldInstance[Block] = ForeignKeyField(
        model_name=Block.Meta.model,
        source_field='created_at_block_id',
        to_field='level',
    )
