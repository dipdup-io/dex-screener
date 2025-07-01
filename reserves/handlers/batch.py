from asyncio import Queue
from copy import copy
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from dipdup.context import DipDupContext
from dipdup.context import HandlerContext
from dipdup.index import MatchedHandler
from dipdup.models.substrate import SubstrateEvent

from reserves.models import BalanceUpdateEvent


def get_recurring_events(event_a: SubstrateEvent, event_b: SubstrateEvent) -> int | bool:
    """
    Returns the index of a redundant Event in a pair of sequential Events to exclude the recurring one from Indexing
    Returns False if the Events are not related to the same balance update
    """
    if event_a.level != event_b.level:
        return False
    name_a, index_a = event_a.name, event_a.data.index
    name_b, index_b = event_b.name, event_b.data.index
    duplicate_conditions = {
        'index': index_a + 1 == index_b,
    }
    params_map = {}
    duplicate_index = 0  # default behavior
    match name_a, name_b:
        case 'Balances.Deposit', 'Currencies.Deposited':
            # jump over Balances.Issued
            # see: https://hydration.subscan.io/extrinsic/7439544-2?event=7439544-52
            duplicate_conditions['index'] = index_b - index_a in (1, 2)
        case 'Balances.Withdraw', 'Currencies.Withdrawn':
            # jump over Balances.Rescinded
            # see: https://hydration.subscan.io/extrinsic/7425606-2?event=7425606-169
            duplicate_conditions['index'] = index_b - index_a in (1, 2)
        case 'Tokens.Withdrawn', 'Currencies.Transferred':
            # Insufficient Withdrawn Event precedes full Transfer Event
            # see: https://hydration.subscan.io/block/7425606?tab=event&event=7425606-2
            duplicate_index = 0
            params_map['b'] = (event_b.payload['currency_id'], event_b.payload['from'], event_b.payload['amount'])
        case 'Balances.Transfer', 'Currencies.Transferred':
            pass
        case 'Tokens.Deposited', 'Currencies.Deposited':
            pass
        case 'Tokens.Withdrawn', 'Currencies.Withdrawn':
            pass
        case 'Tokens.Transfer', 'Currencies.Transferred':
            pass
        case _:
            return False

    for name, payload, key in [(name_a, event_a.payload, 'a'), (name_b, event_b.payload, 'b')]:
        match name:
            case 'Balances.Deposit' | 'Balances.Withdraw':
                payload_copy = copy(payload)
                params = (0, payload_copy.pop('who'), payload_copy.popitem()[1])
            case 'Balances.Transfer':
                payload_copy = copy(payload)
                params = (0, payload_copy.pop('from'), payload_copy.pop('to'), payload_copy.popitem()[1])  # type: ignore[assignment]
            case 'Tokens.Deposited' | 'Currencies.Deposited' | 'Tokens.Withdrawn' | 'Currencies.Withdrawn':
                params = (payload['currency_id'], payload['who'], payload['amount'])
            case 'Tokens.Transfer' | 'Currencies.Transferred':
                params = (payload['currency_id'], payload['from'], payload['to'], payload['amount'])  # type: ignore[assignment]
            case _:
                return False
        params_map = {key: params} | params_map

    duplicate_conditions['params'] = params_map['a'] == params_map['b']

    if not all(duplicate_conditions.values()):
        return False

    return duplicate_index


async def batch(
    ctx: HandlerContext,
    handlers: tuple[MatchedHandler, ...],
) -> None:
    recurring_events_indexes: set[int] = set()
    for index in range(len(handlers) - 1):
        if index in recurring_events_indexes:
            continue
        event_a, event_b = (next(iter(handler.args)) for handler in handlers[index : index + 2])
        pair_index = get_recurring_events(event_a, event_b)
        if pair_index is False:
            continue
        if pair_index in (0, 1):
            recurring_events_indexes.add(index + pair_index)

    if len(recurring_events_indexes) > 0:
        handlers = (handler for index, handler in enumerate(handlers) if index not in recurring_events_indexes)  # type: ignore[assignment]

    for handler in handlers:
        await ctx.fire_matched_handler(handler)

    return

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
    buffer_limit: int = NotImplemented
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
