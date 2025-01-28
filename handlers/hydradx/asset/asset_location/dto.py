from pydantic import BaseModel


class ExternalMetadataDTO(BaseModel):
    name: str
    symbol: str
    decimals: int
