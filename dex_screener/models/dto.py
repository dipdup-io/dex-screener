from collections.abc import Mapping
from datetime import UTC
from datetime import datetime
from typing import Annotated
from typing import Self

from dipdup.models.substrate import SubstrateEvent
from pydantic import BaseModel
from pydantic import Field
from pydantic import computed_field


class DexScreenerEventInfoDTO(BaseModel):
    id: Annotated[int, Field(exclude=True)]
    block_id: int
    # block_datetime: Annotated[datetime | None, Field(exclude=True)]
    timestamp: datetime | None
    tx_index: int

    # @computed_field
    # @property
    # def timestamp(self) -> int | None:
    #     if self.block_datetime is not None:
    #         return int(self.block_datetime.timestamp())
    #     return None

    @computed_field
    @property
    def tx_id(self) -> str:
        return f'{self.block_id}-{self.tx_index}'

    @computed_field
    @property
    def event_index(self) -> str:
        return f'{self.block_id}-{self.id}'

    @classmethod
    def from_event(cls, event: SubstrateEvent) -> Self:
        return cls(
            id=event.data.index,
            block_id=event.level,
            timestamp=cls._get_block_datetime(event),
            tx_index=cls._get_tx_index(event),
        )

    @classmethod
    def _get_block_datetime(cls, event: SubstrateEvent) -> datetime | None:
        if isinstance(event.data.header_extra, Mapping):
            timestamp_ms = event.data.header_extra['timestamp']
            return datetime.fromtimestamp(timestamp=timestamp_ms / 1000, tz=UTC)
        return None
    @classmethod
    def _get_tx_index(cls, event: SubstrateEvent) -> int:
        if event.data.extrinsic_index is not None:
            return event.data.extrinsic_index
        return 0
