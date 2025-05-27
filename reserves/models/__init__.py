from dipdup import fields
from dipdup.models import Model
from dipdup.models.substrate import SubstrateEvent
from scalecodec import ss58_decode  # type: ignore[import-untyped]

RUNTIME_BALANCE_MAX_DIGITS = len(str(2**128 - 1))


class BalanceHistory(Model):
    class Meta:
        table = 'balance_history'
        model = 'models.BalanceHistory'

    id = fields.BigIntField(primary_key=True)

    asset_account = fields.CharField(max_length=77)
    asset_id = fields.IntField()
    account = fields.CharField(max_length=66)

    balance = fields.DecimalField(max_digits=RUNTIME_BALANCE_MAX_DIGITS, decimal_places=0)

    @classmethod
    async def insert(cls, account: str, asset_id: int):
        if (len(account) == 48 and account[0] == '7') or not account.startswith('0x'):
            account = f'0x{ss58_decode(account)}'

        group_key = BalanceUpdateEvent.group_key(asset_id, account)

        balance_record = await cls.filter(asset_account=group_key).order_by('-id').first()
        balance = 0 if balance_record is None else balance_record.balance

        balance_update_record = await BalanceUpdateEvent.filter(asset_account=group_key).order_by('-id').first()
        balance_update = 0 if balance_update_record is None else balance_update_record.balance_update
        await cls.create(
            id=balance_update_record.id,  # type: ignore[union-attr]
            asset_account=group_key,
            asset_id=asset_id,
            account=account,
            balance=balance + balance_update,
        )


class SupplyHistory(Model):
    class Meta:
        table = 'supply_history'
        model = 'models.SupplyHistory'

    id = fields.BigIntField(primary_key=True)
    asset_id = fields.IntField()
    supply = fields.DecimalField(max_digits=RUNTIME_BALANCE_MAX_DIGITS, decimal_places=0)

    @classmethod
    async def insert(cls, asset_id: int):
        supply_record = await cls.filter(asset_id=asset_id).order_by('-id').first()
        supply = 0 if supply_record is None else supply_record.supply

        balance_update_record = await BalanceUpdateEvent.filter(asset_id=asset_id).order_by('-id').first()

        await cls.create(
            id=balance_update_record.id,  # type: ignore[union-attr]
            asset_id=asset_id,
            supply=supply + balance_update_record.balance_update,  # type: ignore[union-attr]
        )


class BalanceUpdateEvent(Model):
    class Meta:
        table = 'balance_update_event'
        model = 'models.BalanceUpdateEvent'

    id = fields.BigIntField(
        primary_key=True,
    )

    asset_account = fields.CharField(max_length=77)
    asset_id = fields.IntField()
    account = fields.CharField(max_length=66)

    balance_update = fields.DecimalField(max_digits=RUNTIME_BALANCE_MAX_DIGITS, decimal_places=0)

    @classmethod
    async def insert(cls, event: SubstrateEvent, account: str, asset_id: int, balance_update: int):
        from reserves.handlers.batch import EventBuffer
        from reserves.handlers.batch import RuntimeFlag

        if (len(account) == 48 and account[0] == '7') or not account.startswith('0x'):
            account = f'0x{ss58_decode(account)}'

        event_id = (((event.data.level << 16) + event.data.index) << 1) + int(balance_update > 0)

        if RuntimeFlag.realtime:
            await BalanceUpdateEvent.create(
                id=event_id,
                asset_account=cls.group_key(asset_id, account),
                asset_id=asset_id,
                account=account,
                balance_update=balance_update,
            )
        else:
            record = BalanceUpdateEvent(
                id=event_id,
                asset_account=cls.group_key(asset_id, account),
                asset_id=asset_id,
                account=account,
                balance_update=balance_update,
            )

            EventBuffer.queue.put_nowait(record)

    @staticmethod
    def group_key(asset_id: int, account: str) -> str:
        return f'{asset_id}:{account}'
