from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING

from dex_screener.models import Asset
from dex_screener.service.event.const import DexScreenerEventType
from dex_screener.service.event.entity.abstract_event_entity import DexScreenerEventEntity
from dex_screener.service.event.entity.swap.dto import MarketDataArgsDTO
from dex_screener.service.event.entity.swap.dto import SwapEventMarketDataDTO
from dex_screener.service.event.entity.swap.exception import InvalidSwapEventMarketDataError

if TYPE_CHECKING:
    from dex_screener.models import DexEvent
    from dex_screener.service.event.entity.dto import DexScreenerEventDataDTO
    from dex_screener.service.event.entity.swap.dto import SwapEventPoolDataDTO


class SwapEventEntity(DexScreenerEventEntity, ABC):
    event_type: str = DexScreenerEventType.Swap

    event_data: DexScreenerEventDataDTO = NotImplemented
    pool_data: SwapEventPoolDataDTO = NotImplemented
    market_data: SwapEventMarketDataDTO = NotImplemented

    @abstractmethod
    async def resolve(self):
        self.event_data = await self.resolve_event_data()
        self.pool_data = await self.resolve_pool_data()
        try:
            self.market_data = await self.resolve_market_data()
        except ValueError as exception:
            raise InvalidSwapEventMarketDataError from exception

    @abstractmethod
    async def resolve_pool_data(self) -> SwapEventPoolDataDTO:
        raise NotImplementedError

    @abstractmethod
    async def resolve_market_data(self) -> SwapEventMarketDataDTO:
        raise NotImplementedError

    async def save(self) -> DexEvent:
        from dex_screener.models import DexEvent

        fields = {
            **self.event_data.model_dump(),
            **self.pool_data.model_dump(),
            **self.market_data.model_dump(),
        }
        fields.update({'event_type': self.event_type})

        record: DexEvent = await DexEvent.create(**fields)
        return record

    async def _market_data_from_args(self, args: MarketDataArgsDTO):
        asset_in = await Asset.get(id=args.asset_in_id)
        asset_out = await Asset.get(id=args.asset_out_id)
        asset_amount_in = asset_in.from_minor(args.minor_amount_in)
        asset_amount_out = asset_out.from_minor(args.minor_amount_out)

        if asset_in.id < asset_out.id:
            return SwapEventMarketDataDTO(
                maker=args.maker,
                amount_0_in=str(asset_amount_in),
                amount_1_out=str(asset_amount_out),
                price=str(asset_amount_out / asset_amount_in),
            )

        if asset_in.id > asset_out.id:
            return SwapEventMarketDataDTO(
                maker=args.maker,
                amount_0_out=str(asset_amount_out),
                amount_1_in=str(asset_amount_in),
                price=str(asset_amount_in / asset_amount_out),
            )

        raise InvalidSwapEventMarketDataError(f'Invalid Swap Event: Asset0==Asset1. Payload: {self._event.payload}.')
