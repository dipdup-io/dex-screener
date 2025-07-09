from asyncio import Queue
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from dipdup.context import DipDupContext
from dipdup.context import HandlerContext
from dipdup.index import MatchedHandler

from reserves.models import BalanceUpdateEvent


async def batch(
    ctx: HandlerContext,
    handlers: tuple[MatchedHandler, ...],
) -> None:
    for handler in handlers:
        await ctx.fire_matched_handler(handler)

    # return

    if not RuntimeFlag.realtime:
        if EventBuffer.filled():
            await EventBuffer.flush(ctx)

        if not RuntimeFlag.synchronized and RuntimeFlag.history_refresh_condition():
            ctx.logger.info('Processing refresh of `balance_history` and `supply_history`...')
            await refresh_history(ctx)
            RuntimeFlag.history_set_next_refresh(ctx)
        if RuntimeFlag.synchronized:
            ctx.logger.info(
                'Processing final refresh of `balance_history` and `supply_history` before switch to realtime updates...'
            )
            await refresh_history(ctx)
            RuntimeFlag.realtime = True


async def refresh_history(ctx: HandlerContext):
    await EventBuffer.flush(ctx)
    refresh_start = datetime.now()
    await ctx.execute_sql_script('on_refresh_history')
    refresh_duration = datetime.now() - refresh_start
    ctx.logger.info('Tables `balance_history` and `supply_history` are successfully updated in %s', refresh_duration)


class RuntimeFlag:
    realtime: bool = False
    synchronized: bool = False
    history_refresh_at: datetime = datetime.now(UTC)
    history_refresh_period: timedelta = timedelta(minutes=10)

    @classmethod
    def history_refresh_condition(cls) -> bool:
        return datetime.now(UTC) >= cls.history_refresh_at

    @classmethod
    def history_set_next_refresh(cls, ctx: DipDupContext) -> datetime:
        cls.history_refresh_at = datetime.now(UTC).replace(microsecond=0) + cls.history_refresh_period
        ctx.logger.info('Next history refresh is scheduled at %s.', cls.history_refresh_at)
        return cls.history_refresh_at


class EventBuffer:
    buffer_limit: int = 10000
    queue: Queue[BalanceUpdateEvent] = Queue()

    @classmethod
    async def flush(cls, ctx: DipDupContext):
        ctx.logger.info('Flushing EventBuffer to DB...')
        q = cls.queue
        event_batch: list[BalanceUpdateEvent] = []
        while not q.empty():
            event_batch.append(q.get_nowait())

        if event_batch:
            latest_record: BalanceUpdateEvent = event_batch[-1]
            model_class: type[BalanceUpdateEvent] = type(latest_record)
            await model_class.bulk_create(event_batch)
            ctx.logger.info(
                'Bulk-inserted %d Events to `%s` with latest id %s.',
                len(event_batch),
                model_class.Meta.table,
                latest_record.id,
            )
        assert cls.queue.empty()
        del event_batch

    @classmethod
    def filled(cls):
        return cls.queue.qsize() > cls.buffer_limit
