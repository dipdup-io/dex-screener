from pydantic import BaseModel

# from pydantic import computed_field


class DexScreenerEventDataDTO(BaseModel):
    event_index: int
    name: str
    block_id: int
    tx_index: int
    #
    # @computed_field
    # @property
    # def id(self) -> int:
    #     return self.block_id << 16 + self.event_index
