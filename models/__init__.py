from dipdup import fields
from dipdup.models import Model


class Asset(Model):
    class Meta:
        table = 'asset'
        model = 'models.Asset'

    id = fields.IntField(primary_key=True)
    name = fields.TextField()


class Event(Model):
    class Meta:
        table = 'event'
        model = 'models.Event'

    id = fields.IntField(primary_key=True)
    who = fields.TextField()
    asset_id = fields.IntField()
    asset_out = fields.IntField()
    amount_id = fields.TextField()
    amount_out = fields.TextField()
