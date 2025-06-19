#!/usr/bin/env python3

import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
import orjson
from dipdup.utils import json_dumps
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import Response

_logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Configuration for the HTTP proxy"""

    client_host: str = 'hasura'
    client_port: str = '8080'
    server_url_path: str = '/api/rest'
    server_host: str = '0.0.0.0'
    server_port: str = '8000'


def create_api(config: ProxyConfig) -> FastAPI:
    """Create FastAPI application with the given configuration"""

    _logger.info('Creating API with config: %s', config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage HTTP client lifecycle"""
        async with httpx.AsyncClient(base_url=f'http://{config.client_host}:{config.client_port}') as client:
            app.state.client = client
            yield

    app = FastAPI(lifespan=lifespan)
    base_route = APIRouter(prefix=config.server_url_path)

    @base_route.get('/latest-block')
    async def forward_latest_block(request: Request):
        return await forward_request(request)

    @base_route.get('/asset')
    async def forward_asset(request: Request):
        return await forward_request(request)

    @base_route.get('/pair')
    async def forward_pair(request: Request):
        return await forward_request(request)

    @base_route.get('/events')
    async def forward_events(request: Request):
        return await forward_request(request, clean_json)

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
        if (reserves := item.get('reserves')) is not None:
            if reserves.get('asset0') is None or reserves.get('asset0') == 'None':
                reserves.pop('asset0', None)
            if reserves.get('asset1') is None or reserves.get('asset1') == 'None':
                reserves.pop('asset1', None)
            if len(reserves) < 2:
                item.pop('reserves', None)
    return data


def clean_json(data: bytes) -> bytes:
    """Clean JSON data by removing None fields and returning bytes"""
    try:
        json_data = orjson.loads(data)
        cleaned_data = remove_none_fields(json_data)
        return json_dumps(cleaned_data, None)
    except orjson.JSONDecodeError as e:
        _logger.error('Failed to decode JSON content: ', e)
        return data
    except Exception as e:
        _logger.error('Error processing data: ', e)
        return data


async def forward_request(
    request: Request,
    transform: Callable[[bytes], bytes] | None = None,
) -> Response:
    # Forward request with exact headers and body
    client: httpx.AsyncClient = request.app.state.client
    url = httpx.URL(path=request.url.path)
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
    response = await client.send(forwarded_request)

    headers = response.headers.copy()
    headers.pop('Content-Encoding', None)

    if transform:
        # Read JSON content
        content = await response.aread()
        data = transform(content)

        headers['Content-Length'] = str(len(data)) if data else '0'
    else:
        data = await response.aread()

    return Response(
        data,
        status_code=response.status_code,
        headers=headers,
    )
