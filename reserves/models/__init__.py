import logging

from dipdup import fields
from dipdup.models import Model
from dipdup.models.substrate import SubstrateEvent
from lru import LRU
from scalecodec import ss58_decode

RUNTIME_BALANCE_MAX_DIGITS = len(str(2**128 - 1))


class BalanceHistory(Model):
    class Meta:
        table = 'balance_history'
        model = 'models.BalanceHistory'

    id = fields.BigIntField(primary_key=True)
    account = fields.CharField(max_length=66, db_index=True)
    asset_id = fields.IntField(db_index=True)
    balance = fields.DecimalField(max_digits=RUNTIME_BALANCE_MAX_DIGITS, decimal_places=0)

    @classmethod
    async def insert(cls, account: str, asset_id: int):
        if (len(account) == 48 and account[0] == '7') or not account.startswith('0x'):
            account = f'0x{ss58_decode(account)}'

        balance_record = await cls.filter(account=account, asset_id=asset_id).order_by('-id').first()
        balance = 0 if balance_record is None else balance_record.balance

        balance_update_record = (
            await BalanceUpdateEvent.filter(account=account, asset_id=asset_id).order_by('-id').first()
        )

        await cls.create(
            id=balance_update_record.id,
            account=account,
            asset_id=asset_id,
            balance=balance + balance_update_record.balance_update,
        )


class SupplyHistory(Model):
    class Meta:
        table = 'supply_history'
        model = 'models.SupplyHistory'

    id = fields.BigIntField(primary_key=True)
    asset_id = fields.IntField(db_index=True)
    supply = fields.DecimalField(max_digits=RUNTIME_BALANCE_MAX_DIGITS, decimal_places=0)

    @classmethod
    async def insert(cls, asset_id: int):
        supply_record = await cls.filter(asset_id=asset_id).order_by('-id').first()
        supply = 0 if supply_record is None else supply_record.supply

        balance_update_record = await BalanceUpdateEvent.filter(asset_id=asset_id).order_by('-id').first()

        await cls.create(
            id=balance_update_record.id,
            asset_id=asset_id,
            supply=supply + balance_update_record.balance_update,
        )


class BalanceUpdateEvent(Model):
    class Meta:
        table = 'balance_update_event'
        model = 'models.BalanceUpdateEvent'

    id = fields.BigIntField(primary_key=True)

    account = fields.CharField(max_length=66, db_index=True)
    asset_id = fields.IntField(db_index=True)

    balance_update = fields.DecimalField(max_digits=RUNTIME_BALANCE_MAX_DIGITS, decimal_places=0)

    @classmethod
    async def insert(cls, event: SubstrateEvent, account: str, asset_id: int, balance_update: int):
        if (len(account) == 48 and account[0] == '7') or not account.startswith('0x'):
            account = f'0x{ss58_decode(account)}'

        event_id = (((event.data.level << 16) + event.data.index) << 1) + int(balance_update > 0)

        await BalanceUpdateEvent.create(
            id=event_id,
            account=account,
            asset_id=asset_id,
            balance_update=balance_update,
        )
