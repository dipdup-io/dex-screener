import logging
from collections.abc import Awaitable
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
import orjson
from asyncache import cached  # type: ignore[import-untyped]
from cachetools import TTLCache
from dipdup.utils import json_dumps
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import Response

from dex_screener import utils

_logger = logging.getLogger(__name__)
_client: httpx.AsyncClient | None = None


# TODO: Tune values
BALANCES_CACHE_SIZE = 10000
POOL_CACHE_SIZE = 10000
SUPPLY_CACHE_SIZE = 10000
DECIMALS_CACHE_SIZE = 10000

CACHE_TTL = 60 * 60


# NOTE: Cached versions of utility functions.
get_pool_by_pair = cached(
    cache=TTLCache(maxsize=POOL_CACHE_SIZE, ttl=CACHE_TTL),
)(utils.get_pool_by_pair)

get_balance_by_account = cached(
    cache=TTLCache(maxsize=BALANCES_CACHE_SIZE, ttl=CACHE_TTL),
)(utils.get_balance_by_account)

get_asset_supply = cached(
    cache=TTLCache(maxsize=SUPPLY_CACHE_SIZE, ttl=CACHE_TTL),
)(utils.get_asset_supply)

get_decimals_by_asset_id = cached(
    cache=TTLCache(maxsize=DECIMALS_CACHE_SIZE, ttl=CACHE_TTL),
)(utils.get_decimals_by_asset_id)


@dataclass
class ProxyConfig:
    """Configuration for the HTTP proxy service. Parsed from `config.custom['proxy']`."""

    hasura_host: str = 'hasura'
    hasura_port: str = '8080'
    server_url_path: str = '/api/rest'
    server_host: str = '0.0.0.0'
    server_port: str = '8000'


def create_api(config: ProxyConfig) -> FastAPI:
    """Create FastAPI application with the given configuration"""

    _logger.info('Creating API with config: %s', config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _client

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


def process_hasura_response(data: dict[str, Any]) -> dict[str, Any]:
    events = data.get('events', [])
    if not events:
        return data

    for item in events:
        # NOTE: dex_screener specification requires nulls to be removed from the response
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

        if item.get('reserves', {}).get('asset0') is None:
            item.get('reserves', {}).pop('asset0', None)
        if item.get('reserves', {}).get('asset1') is None:
            item.get('reserves', {}).pop('asset1', None)
        if not item.get('reserves'):
            item.pop('reserves', None)

        # FIXME: stableswap hack
        if ':' in item.get('pool', {}).get('account', ''):
            account, pool_id = item['pool']['account'].split(':', 1)
            item['pool']['account'] = account
            item['pool']['id'] = pool_id
    return data


async def transform_events(
    data: bytes,
) -> bytes:
    """Transform the response from Hasura to match the dex_screener specification."""
    json_data = orjson.loads(data)
    processed_data = process_hasura_response(json_data)
    return json_dumps(processed_data, None)


async def forward_request(
    request: Request,
    config: ProxyConfig,
    transform: Callable[[bytes], Awaitable[bytes]] | None = None,
) -> Response:
    """Forward request to the configured Hasura instance and optionally transform the response."""
    client: httpx.AsyncClient = request.app.state.client
    url = httpx.URL(f'http://{config.hasura_host}:{config.hasura_port}{request.url.path}')
    forwarded_request = client.build_request(
        method=request.method,
        url=url,
        headers=request.headers.raw,
        params=request.query_params,
        content=request.stream(),
    )
    _logger.info('Forwarding request to %s', forwarded_request.url)
    response = await _client.send(forwarded_request)  # type: ignore[union-attr]

    headers = response.headers.copy()
    headers.pop('Content-Encoding', None)

    data = await response.aread()
    if transform:
        data = await transform(data)

        headers['Content-Length'] = str(len(data)) if data else '0'

    return Response(
        data,
        status_code=response.status_code,
        headers=headers,
    )
