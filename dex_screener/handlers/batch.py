from __future__ import annotations

from typing import TYPE_CHECKING

from dipdup.config.substrate_events import SubstrateEventsHandlerConfig

from dex_screener.models import Block

if TYPE_CHECKING:
    from collections.abc import Iterable

    from dipdup.context import HandlerContext
    from dipdup.index import MatchedHandler


class DeprecatedEvent:
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
    done: bool = False
    level: int = 6837788


class DeprecatedBroadcastSwapped:
    names = ('Broadcast.Swapped',)
    done: bool = False
    level: int = 7342919


async def batch(
    ctx: HandlerContext,
    handlers: Iterable[MatchedHandler],
) -> None:
    if DeprecatedEvent.done or handlers[0].level < DeprecatedEvent.level:
        pass
    else:
        ctx.config.indexes['hydradx_events'].handlers = tuple(
            [hc for hc in ctx.config.indexes['hydradx_events'].handlers if hc.name not in DeprecatedEvent.names]
        )
        handlers = tuple(
            [
                mh
                for mh in handlers
                if mh.index.name == 'hydradx_events'
                and isinstance(mh.config, SubstrateEventsHandlerConfig)
                and mh.config.name not in DeprecatedEvent.names
            ]
        )
        DeprecatedEvent.done = True

    if DeprecatedBroadcastSwapped.done or handlers[0].level < DeprecatedBroadcastSwapped.level:
        pass
    else:
        ctx.config.indexes['hydradx_events'].handlers = tuple(
            [hc for hc in ctx.config.indexes['hydradx_events'].handlers if hc.name not in DeprecatedBroadcastSwapped.names]
        )
        handlers = tuple(
            [
                mh
                for mh in handlers
                if mh.index.name == 'hydradx_events'
                and isinstance(mh.config, SubstrateEventsHandlerConfig)
                and mh.config.name not in DeprecatedBroadcastSwapped.names
            ]
        )
        DeprecatedBroadcastSwapped.done = True

    batch_levels = []
    for handler in handlers:
        if handler.level not in batch_levels and handler.config.name[:10] != 'Currencies':
            try:
                timestamp = int(handler.args[0].data.header_extra['timestamp'] // 1000)
            except (KeyError, AttributeError, ValueError, TypeError):
                timestamp = None

            await Block.create(
                level=handler.level,
                timestamp=timestamp,
            )
            batch_levels.append(handler.level)

        await ctx.fire_matched_handler(handler)
