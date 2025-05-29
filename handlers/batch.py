from __future__ import annotations

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING

from dipdup.config.substrate_events import SubstrateEventsHandlerConfig

from dex_screener.models import Block

if TYPE_CHECKING:
    from dipdup.context import HandlerContext
    from dipdup.index import MatchedHandler


class DeprecatedEvent:
    names: tuple[str, ...] = NotImplemented
    done: bool = False
    level: int = NotImplemented


class DexSwapEvent(DeprecatedEvent):
    names = (
        'Omnipool.BuyExecuted',
        'Omnipool.SellExecuted',
        'Stableswap.BuyExecuted',
        'Stableswap.SellExecuted',
        'XYK.BuyExecuted',
        'XYK.SellExecuted',
        'LBP.BuyExecuted',
        'LBP.SellExecuted',
        'OTC.Filled',
        'OTC.PartiallyFilled',
    )
    level: int = 6837788


class BroadcastSwapped(DeprecatedEvent):
    names = ('Broadcast.Swapped',)
    level: int = 7342919


class BroadcastSwapped2(DeprecatedEvent):
    names = ('Broadcast.Swapped2',)
    level: int = 7582524


deprecations = [  # Must be sorted by `level` value
    DexSwapEvent,
    BroadcastSwapped,
    BroadcastSwapped2,
]


async def batch(
    ctx: HandlerContext,
    handlers: tuple[MatchedHandler, ...],
) -> None:
    current_level = handlers[0].level
    for deprecated in deprecations:
        if current_level <= deprecated.level:
            break
        if deprecated.done:
            continue
        # Sweep all `hydradx_events` Index handlers and remove deprecated ones from Index Config (no more matched handlers until restart)
        ctx.config.indexes['hydradx_events'].handlers = tuple(  # type: ignore[attr-defined]
            [hc for hc in ctx.config.indexes['hydradx_events'].handlers if hc.name not in deprecated.names]  # type: ignore[attr-defined]
        )
        # Remove already matched handlers for deprecated events (just for current level)
        handlers = tuple(
            [
                mh
                for mh in handlers
                if mh.index.name == 'hydradx_events'
                and isinstance(mh.config, SubstrateEventsHandlerConfig)
                and mh.config.name not in deprecated.names
            ]
        )
        deprecated.done = True

    batch_levels: set[int] = set()
    for handler in handlers:
        if handler.level not in batch_levels:
            try:
                timestamp = int(handler.args[0].data.header_extra['timestamp'] // 1000)  # type: ignore[index]
            except (KeyError, AttributeError, ValueError, TypeError):
                timestamp = None

            await Block.create(
                level=handler.level,
                timestamp=timestamp,
            )
            batch_levels.add(handler.level)

        try:
            await ctx.fire_matched_handler(handler)
        except Exception as exception:
            ctx.logger.error('Event Processing Error for: %s.', handler.args)
            raise exception

    if RuntimeFlag.blocks_refresh_condition():
        ctx.logger.info('Processing refresh `dex_block`...')
        await ctx.execute_sql_script('refresh_blocks.01_drop_unused_blocks')

        for _ in range(10):
            levels: list[int] = (
                await Block.filter(timestamp__isnull=True).order_by('level').limit(100).values_list('level', flat=True)  # type: ignore[assignment]
            )
            if len(levels) == 0:
                break
            request_payload = {
                'query': ' '.join(
                    [
                        'query { blocks(where: {height_in:',
                        str(levels),
                        '}) { height timestamp } }',
                    ]
                ),
            }

            explorer = ctx.get_http_datasource('explorer')
            response = await explorer.request('post', 'graphql', json=request_payload)

            blocks = [
                Block(
                    level=block_data['height'],
                    timestamp=datetime.fromisoformat(block_data['timestamp']).timestamp(),
                )
                for block_data in response['data']['blocks']
            ]
            if len(blocks) == 0:
                ctx.logger.info('No blocks found for levels: %s.', levels)
                break

            await Block.bulk_update(objects=blocks, fields=['timestamp'])

        await ctx.execute_sql_script('refresh_blocks.00_refresh_latest_block')

        next_refresh_at = RuntimeFlag.blocks_set_next_refresh()
        ctx.logger.info('Next blocks refresh is scheduled at %s.', next_refresh_at)


class RuntimeFlag:
    blocks_refresh_at: datetime = datetime.now(UTC)
    blocks_refresh_period: timedelta = timedelta(seconds=60)

    @classmethod
    def blocks_refresh_condition(cls) -> bool:
        return datetime.now(UTC) >= cls.blocks_refresh_at

    @classmethod
    def blocks_set_next_refresh(cls) -> datetime:
        cls.blocks_refresh_at = datetime.now(UTC).replace(microsecond=0) + cls.blocks_refresh_period
        return cls.blocks_refresh_at
