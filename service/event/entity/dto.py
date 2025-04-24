from pydantic import BaseModel


class DexScreenerEventDataDTO(BaseModel):
    event_index: int
    name: str
    block_id: int
    tx_index: int
