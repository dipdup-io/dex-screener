from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from dipdup import fields
from dipdup.fields import ForeignKeyField
from dipdup.fields import ManyToManyField
from dipdup.fields import OneToOneField
from dipdup.models import Model

from dex_screener.models.dex_fields import AssetAmountField
from dex_screener.models.dex_fields import AssetPriceField
from dex_screener.service.event.const import DexScreenerEventType

if TYPE_CHECKING:
    from tortoise.fields.relational import ForeignKeyFieldInstance
    from tortoise.fields.relational import ManyToManyFieldInstance
    from tortoise.fields.relational import OneToOneFieldInstance

    from dex_screener.handlers.hydradx.asset.asset_count.types import AnyTypeAmount


from dex_screener.handlers.hydradx.asset.asset_count.asset_amount import AssetAmount
from dex_screener.handlers.hydradx.asset.asset_type.enum import HydrationAssetType
from dex_screener.models.dex_fields import AccountField as AccountField
from dex_screener.models.enum import DexKey as DexKey


class Block(Model):
    class Meta:
        table = 'dex_block'
        model = 'models.Block'

    level = fields.IntField(primary_key=True)
    timestamp = fields.IntField(null=True)


class LatestBlock(Model):
    class Meta:
        table = 'ds_latest_block'
        model = 'models.LatestBlock'

    id = fields.BooleanField(primary_key=True)
    block_number = fields.IntField()
    block_timestamp = fields.IntField()


class Asset(Model):
    class Meta:
        table = 'dex_asset'
        model = 'models.Asset'

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, null=True)
    symbol = fields.CharField(max_length=63, null=True)
    decimals = fields.SmallIntField(null=True, default=0)  # fixme
    asset_type = fields.EnumField(enum_type=HydrationAssetType, db_index=True)

    updated_at_block: ForeignKeyFieldInstance[Block] = ForeignKeyField(
        model_name=Block.Meta.model,
        source_field='updated_at_block_id',
        to_field='level',
    )

    def amount(self, amount: AnyTypeAmount) -> AssetAmount:
        return AssetAmount(asset=self, amount=amount)  # type: ignore[arg-type]

    def from_minor(self, minor_amount: AnyTypeAmount) -> AssetAmount:
        amount = Decimal(int(minor_amount)) / 10**self.decimals
        return self.amount(amount=amount)

    def to_minor(self, amount: AssetAmount) -> int:
        return int(amount.shift(self.decimals))

    def __str__(self) -> str:
        caption_list: list[str] = list(filter(None, [self.symbol, self.name, f'Asset(id={self.id})']))
        return caption_list[0]


class Pool(Model):
    class Meta:
        table = 'dex_pool'
        model = 'models.Pool'
        unique_together = ('dex_key', 'dex_pool_id')

    account = AccountField(primary_key=True)
    dex_key = fields.EnumField(enum_type=DexKey, db_index=True)
    dex_pool_id = fields.TextField(db_index=True)
    assets: ManyToManyFieldInstance[Asset] = ManyToManyField(
        model_name=Asset.Meta.model,
        through='dex_asset_pool_reserve',
        forward_key='asset_id',
        backward_key='pool_id',
        related_name='pools',
    )
    lp_token: OneToOneFieldInstance[Asset] = OneToOneField(  # type: ignore[assignment]
        model_name=Asset.Meta.model,
        related_name='liquidity_pool',
        to_field='id',
        source_field='lp_token_id',
        null=True,
    )
    lp_token_id: int

    def __repr__(self) -> str:
        return f'<Pool[{self.dex_key}](id={self.dex_pool_id}, account={self.account})>'


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
        to_field='account',
        related_name='reserves',
    )
    reserve = AssetAmountField(default='0')


class Pair(Model):
    class Meta:
        table = 'dex_pair'
        model = 'models.Pair'
        unique_together = ('pool', 'asset_0', 'asset_1')

    id = fields.CharField(primary_key=True, max_length=100)
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
        to_field='account',
    )

    created_at_block: ForeignKeyFieldInstance[Block] = ForeignKeyField(
        model_name=Block.Meta.model,
        source_field='created_at_block_id',
        to_field='level',
    )
    created_at_tx_id = fields.IntField()
    fee_bps = fields.IntField(null=True)

    def __repr__(self) -> str:
        return f'<Pair[{self.dex_key}]({self.asset_0}/{self.asset_1})>'

    async def get_reserves(self) -> tuple[str, str]:
        await self.fetch_related('asset_0', 'asset_1', 'pool')
        asset_0_minor_reserve = await AssetPoolReserve.get(pool=self.pool, asset=self.asset_0).values_list(
            'reserve', flat=True
        )
        asset_1_minor_reserve = await AssetPoolReserve.get(pool=self.pool, asset=self.asset_1).values_list(
            'reserve', flat=True
        )
        if asset_0_minor_reserve is None:
            asset_0_reserve = None
        else:
            asset_0_reserve = self.asset_0.from_minor(asset_0_minor_reserve)  # type: ignore[arg-type]

        if asset_1_minor_reserve is None:
            asset_1_reserve = None
        else:
            asset_1_reserve = self.asset_1.from_minor(asset_1_minor_reserve)  # type: ignore[arg-type]
        return str(asset_0_reserve), str(asset_1_reserve)


class DexEvent(Model):
    class Meta:
        table = 'dex_event'
        model = 'models.DexEvent'

    id = fields.IntField(primary_key=True)
    event_type = fields.EnumField(DexScreenerEventType, db_index=True)
    name = fields.CharField(max_length=32)
    maker = AccountField()
    pair: ForeignKeyFieldInstance[Pair] = ForeignKeyField(
        model_name=Pair.Meta.model,
        source_field='pair_id',
        to_field='id',
    )

    amount_0_in = AssetAmountField(null=True)
    amount_1_in = AssetAmountField(null=True)
    amount_0_out = AssetAmountField(null=True)
    amount_1_out = AssetAmountField(null=True)
    price = AssetPriceField(null=True)

    amount_0 = AssetAmountField(null=True)
    amount_1 = AssetAmountField(null=True)

    asset_0_reserve = AssetAmountField(null=True)
    asset_1_reserve = AssetAmountField(null=True)

    event_index = fields.IntField(db_index=True)
    tx_index = fields.IntField(db_index=True)
    block: ForeignKeyFieldInstance[Block] = ForeignKeyField(
        model_name=Block.Meta.model,
        source_field='block_id',
        to_field='level',
    )
    metadata = fields.JSONField(null=True)

    block_id: int
    pair_id: int

    def __repr__(self) -> str:
        return f'<{self.event_type!s}Event[{self.name}]({self.block_id}-{self.event_index})>'


class DexOmnipoolPosition(Model):
    class Meta:
        table = 'dex_omnipool_position'
        model = 'models.DexOmnipoolPosition'

    position_id = fields.IntField(primary_key=True)
    owner = AccountField()
    asset_id = fields.IntField()
    amount = AssetAmountField()
    shares = AssetAmountField()
    created = fields.BooleanField(db_index=True, default=False)
