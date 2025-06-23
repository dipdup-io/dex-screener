#!/usr/bin/env python3

import logging
from collections.abc import Awaitable
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
import orjson
from asyncache import cached  # type: ignore[import-untyped]`
from cachetools import Cache
from cachetools import TTLCache
from dipdup.utils import json_dumps
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import Response

CACHE_SIZE = 10000
CACHE_TTL = 60 * 60  # 1 hour

_logger = logging.getLogger(__name__)
_client: httpx.AsyncClient | None = None


class ReservesReceivingError(Exception):
    """Custom exception for errors in receiving reserves data"""

    pass


@dataclass
class ProxyConfig:
    """Configuration for the HTTP proxy"""

    client_host: str = 'hasura'
    client_port: str = '8080'
    server_url_path: str = '/api/rest'
    server_host: str = '0.0.0.0'
    server_port: str = '8000'

    data_url_indexer: str = 'http://hasura:8080/v1/graphql'
    data_url_reserves: str = 'http://hasura_reserves:8080/v1/graphql'


def create_api(config: ProxyConfig) -> FastAPI:
    """Create FastAPI application with the given configuration"""

    _logger.info('Creating API with config: %s', config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _client

        """Manage HTTP client lifecycle"""
        async with httpx.AsyncClient() as client:
            app.state.client = client
            _client = client
            yield

    app = FastAPI(lifespan=lifespan)
    base_route = APIRouter(prefix=config.server_url_path)

    @base_route.get('/latest-block')
    async def forward_latest_block(request: Request):
        return await forward_request(request, config)

    @base_route.get('/asset')
    async def forward_asset(request: Request):
        return await forward_request(request, config)

    @base_route.get('/pair')
    async def forward_pair(request: Request):
        return await forward_request(request, config)

    @base_route.get('/events')
    async def forward_events(request: Request):
        return await forward_request(request, config, transform=transform_events)

    app.include_router(base_route)

    return app


def remove_none_fields(data: Any) -> Any:
    # NOTE: remove reserves field when empty
    # NOTE: remove fields amount0 and amount1 for swap event type
    # NOTE: assetin and assetout 2 fields out of four should be presented (remove asset0In, asset0Out, asset1In, asset1Out if None)
    events = data.get('events', [])
    if not events:
        return data

    for item in events:
        if item.get('eventType') == 'swap':
            item.pop('amount0', None)
            item.pop('amount1', None)
        if item.get('asset0In') is None:
            item.pop('asset0In', None)
        if item.get('asset0Out') is None:
            item.pop('asset0Out', None)
        if item.get('asset1In') is None:
            item.pop('asset1In', None)
        if item.get('asset1Out') is None:
            item.pop('asset1Out', None)
        if item.get('priceNative') is None:
            item.pop('priceNative', None)
        if (reserves := item.get('reserves')) is not None:
            if reserves.get('asset0') in (None, 'None'):
                reserves.pop('asset0', None)
            if reserves.get('asset1') in (None, 'None'):
                reserves.pop('asset1', None)
            if len(reserves) < 2:
                item.pop('reserves', None)
    return data


@cached(cache=Cache(CACHE_SIZE))
async def get_pool_from_pair(url: str, pair_id: str) -> tuple[int, int, str, int]:
    try:
        r = await _client.post(  # type: ignore[union-attr]
            url,
            json={
                'query': """
                    query ReserveID($pair_id: String!) {
                      dex_pair(where: {id: {_eq: $pair_id}}) {
                        asset_0_id
                        asset_1_id
                        dex_pool {
                          dex_pool_id
                          lp_token_id
                        }
                      }
                    }
                """,
                'variables': {'pair_id': pair_id},
            },
        )
    except httpx.RequestError as e:
        raise ReservesReceivingError(f'Failed to get pool from pair {pair_id}') from e
    if r.status_code != 200:
        raise ReservesReceivingError(f'Error response from indexer for pair {pair_id}: {r.status_code} {r.text}')
    result = r.json()
    if not result.get('data', {}).get('dex_pair'):
        raise ReservesReceivingError(f'No pool found for pair {pair_id}')
    pair_data = result['data']['dex_pair'][0]
    return (
        pair_data['asset_0_id'],
        pair_data['asset_1_id'],
        pair_data['dex_pool']['dex_pool_id'],
        pair_data['dex_pool']['lp_token_id'],
    )


@cached(cache=TTLCache(CACHE_SIZE, CACHE_TTL))
async def get_reserves_by_id(url: str, asset_pool: str) -> str:
    try:
        r = await _client.post(  # type: ignore[union-attr]
            url,
            json={
                'query': """
                    query GetReserves($asset_pool: String!) {
                      balanceHistory(limit: 1, order_by: {id: desc}, where: {assetAccount: {_eq: $asset_pool}}) {
                        balance
                      }
                    }
                """,
                'variables': {'asset_pool': asset_pool},
            },
        )
    except httpx.RequestError as e:
        raise ReservesReceivingError(f'Failed to get reserves for asset pool {asset_pool}') from e
    if r.status_code != 200:
        raise ReservesReceivingError(
            f'Error response from indexer for asset pool {asset_pool}: {r.status_code} {r.text}'
        )
    result = r.json()
    if not result.get('data', {}).get('balanceHistory'):
        raise ReservesReceivingError(f'No reserves found for asset pool {asset_pool}')
    return result['data']['balanceHistory'][0]['balance']


@cached(cache=TTLCache(CACHE_SIZE, CACHE_TTL))
async def get_reserves_by_lp(url: str, lp_token_id: int) -> str:
    try:
        r = await _client.post(  # type: ignore[union-attr]
            url,
            json={
                'query': """
                    query GetReservesLP($lp_token_id: Int) {
                      supplyHistory(order_by: {id: desc}, limit: 1, where: {assetId: {_eq: $lp_token_id}}) {
                        supply
                      }
                    }
                """,
                'variables': {'lp_token_id': lp_token_id},
            },
        )
    except httpx.RequestError as e:
        raise ReservesReceivingError(f'Failed to get reserves for LP token {lp_token_id}') from e
    if r.status_code != 200:
        raise ReservesReceivingError(
            f'Error response from indexer for LP token {lp_token_id}: {r.status_code} {r.text}'
        )
    result = r.json()
    if not result.get('data', {}).get('supplyHistory'):
        raise ReservesReceivingError(f'No reserves found for LP token {lp_token_id}')
    return result['data']['supplyHistory'][0]['supply']


@cached(cache=Cache(CACHE_SIZE))
async def get_decimals_by_asset_id(url: str, asset_id: int) -> int:
    try:
        r = await _client.post(  # type: ignore[union-attr]
            url,
            json={
                'query': """
                    query GetDecimals($asset_id: Int) {
                      dex_asset(where: {id: {_eq: $asset_id}}) {
                        decimals
                      }
                    }
                """,
                'variables': {'asset_id': asset_id},
            },
        )
    except httpx.RequestError as e:
        raise ReservesReceivingError(f'Failed to get decimals for asset {asset_id}') from e
    if r.status_code != 200:
        raise ReservesReceivingError(f'Error response from indexer for asset {asset_id}: {r.status_code} {r.text}')
    result = r.json()
    if not result.get('data', {}).get('dex_asset'):
        raise ReservesReceivingError(f'No asset found for id {asset_id}')

    return result['data']['dex_asset'][0]['decimals']


async def add_reserves_to_events(data: Any, config: ProxyConfig, client: httpx.AsyncClient) -> Any:
    for event in data.get('events', []):
        try:
            asset0_id, asset1_id, pool_id, lp_token_id = await get_pool_from_pair(
                config.data_url_indexer, event['pairId']
            )

            if asset0_id != lp_token_id:
                asset0_reserves = await get_reserves_by_id(config.data_url_reserves, f'{asset0_id}:{pool_id}')
            else:
                asset0_reserves = await get_reserves_by_lp(config.data_url_reserves, asset0_id)
            if asset1_id != lp_token_id:
                asset1_reserves = await get_reserves_by_id(config.data_url_reserves, f'{asset1_id}:{pool_id}')
            else:
                asset1_reserves = await get_reserves_by_lp(config.data_url_reserves, asset1_id)

            asset0_decimals = await get_decimals_by_asset_id(config.data_url_indexer, asset0_id)
            asset1_decimals = await get_decimals_by_asset_id(config.data_url_indexer, asset1_id)
            event['reserves'] = {
                'asset0': float(asset0_reserves) / (10**asset0_decimals),
                'asset1': float(asset1_reserves) / (10**asset1_decimals),
            }
        except ReservesReceivingError as e:
            _logger.error('Error receiving reserves data: %s', e)
            continue


async def transform_events(data: bytes, config: ProxyConfig, client: httpx.AsyncClient) -> bytes:
    """Clean JSON data by removing None fields and returning bytes"""
    try:
        json_data = orjson.loads(data)
        cleaned_data = remove_none_fields(json_data)
        await add_reserves_to_events(cleaned_data, config, client)
        return json_dumps(cleaned_data, None)
    except orjson.JSONDecodeError as e:
        _logger.error('Failed to decode JSON content: ', e)
        return data
    except orjson.JSONEncodeError as e:
        _logger.error('Failed to encode JSON content: ', e)
        return data
    except Exception as e:
        _logger.error('Error processing data: ', e)
        return data


async def forward_request(
    request: Request,
    config: ProxyConfig,
    transform: Callable[[bytes, ProxyConfig, httpx.AsyncClient], Awaitable[bytes]] | None = None,
) -> Response:
    # Forward request with exact headers and body
    client: httpx.AsyncClient = request.app.state.client
    url = httpx.URL(f'http://{config.client_host}:{config.client_port}{request.url.path}')
    # header filtering, if we will need it: headers = [(k, v) for k, v in request.headers.raw if k != b'host']
    forwarded_request = client.build_request(
        method=request.method,
        url=url,
        headers=request.headers.raw,
        params=request.query_params,
        # params included in the URL
        content=request.stream(),
    )
    _logger.info('Forwarding request to %s', forwarded_request.url)
    response = await _client.send(forwarded_request)  # type: ignore[union-attr]

    headers = response.headers.copy()
    headers.pop('Content-Encoding', None)

    if transform:
        # Read JSON content
        content = await response.aread()
        data = await transform(content, config, client)

        headers['Content-Length'] = str(len(data)) if data else '0'
    else:
        data = await response.aread()

    return Response(
        data,
        status_code=response.status_code,
        headers=headers,
    )
