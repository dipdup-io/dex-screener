from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from dipdup.models.substrate import SubstrateEvent
from dipdup.models.substrate import SubstrateEventData

from dex_screener.handlers.hydradx.asset.asset_type.exception import InvalidEventDataError
from dex_screener.models import Asset


class AbstractHydrationAsset(ABC):
    asset_type: str = ...

    @classmethod
    @abstractmethod
    async def handle_register_asset(cls, event: SubstrateEvent) -> Asset: ...

    @classmethod
    @abstractmethod
    async def handle_update_asset(cls, event: SubstrateEvent) -> Asset: ...

    @classmethod
    @abstractmethod
    async def create_asset(cls, asset_id: int, event: SubstrateEvent, fields: dict[str, Any] | None) -> Asset: ...

    @classmethod
    @abstractmethod
    async def update_asset(cls, asset_id: int, updated_fields: dict[str, Any], event: SubstrateEvent) -> Asset: ...


class BaseHydrationAsset(AbstractHydrationAsset):
    @classmethod
    async def handle_register_asset(cls, event: SubstrateEvent) -> Asset:
        match event.payload:
            case {
                'asset_id': int(0) as asset_id,
                'asset_name': str(asset_name),
            }:
                return await cls.update_asset(
                    asset_id=asset_id,
                    updated_fields={'name': asset_name},
                    event=event,
                )

            case {
                'asset_id': int(asset_id),
                'name': str(asset_name),
            }:
                pass
            case {
                'asset_id': int(asset_id),
                'asset_name': str(asset_name),
            }:
                pass
            case _:
                raise InvalidEventDataError('Unhandled Event Payload.')

        return await cls.create_asset(asset_id, event, {'name': asset_name})

    @classmethod
    async def handle_update_asset(cls, event: SubstrateEvent) -> Asset:
        match event.payload:
            case {
                'asset_id': int(asset_id),
                'symbol': str(asset_symbol),
                'decimals': int(asset_decimals),
            }:
                updated_fields = {
                    'symbol': asset_symbol,
                    'decimals': asset_decimals,
                }
            case {
                'asset_id': int(asset_id),
                'asset_name': str(asset_name),
            }:
                updated_fields = {
                    'name': asset_name,
                }
            case _:
                raise InvalidEventDataError('Unhandled Event Data.')

        return await cls.update_asset(
            asset_id=asset_id,
            updated_fields=updated_fields,
            event=event,
        )

    @classmethod
    async def create_asset(cls, asset_id: int, event: SubstrateEvent, fields: dict[str, Any] | None = None) -> Asset:
        from .const import PRE_RESOLVED_TOKENS_METADATA

        if fields is None:
            fields = {}

        if asset_id in PRE_RESOLVED_TOKENS_METADATA:
            fields.update(PRE_RESOLVED_TOKENS_METADATA[asset_id])

        return await Asset.create(
            id=asset_id,
            asset_type=cls.asset_type,
            updated_at_block_id=event.level,
            **fields,
        )

    @classmethod
    async def update_asset(cls, asset_id: int, updated_fields: dict[str, Any], event: SubstrateEvent) -> Asset:
        updated_fields.setdefault('asset_type', cls.asset_type)
        updated_fields.setdefault('updated_at_block_id', event.level)
        asset, _ = await Asset.update_or_create(
            id=asset_id,
            defaults=updated_fields,
        )
        return asset


class HexNamedHydrationAsset(BaseHydrationAsset):
    @classmethod
    async def handle_register_asset(cls, event: SubstrateEvent) -> Asset:
        match event:
            case SubstrateEvent(
                data=SubstrateEventData(
                    args={
                        'assetId': int(asset_id),
                        'assetName': str(asset_name),
                    }
                )
            ):
                pass
            case SubstrateEvent(
                payload={
                    'asset_id': int(asset_id),
                    'asset_name': str(asset_name),
                }
            ):
                asset_name = '0x'+asset_name.encode().hex()
                pass

            case _:
                raise InvalidEventDataError('Unhandled Event Data.')

        return await cls.create_asset(asset_id, event, {'name': asset_name})
