#!/usr/bin/env python3

import logging
from collections.abc import Awaitable
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

    data_url_indexer: str = 'https://dex-screener-hydration.piltover.baking-bad.org/v1/graphql'
    data_url_reserves: str = 'https://dex-screener-hydration-reserves.piltover.baking-bad.org/v1/graphql'
    # data_url_indexer: str = 'http://hasura:8080/v1/graphql'
    # data_url_reserves: str = 'http://hasura_reserves:8080/v1/graphql'


def create_api(config: ProxyConfig) -> FastAPI:
    """Create FastAPI application with the given configuration"""

    _logger.info('Creating API with config: %s', config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage HTTP client lifecycle"""
        async with httpx.AsyncClient() as client:
            app.state.client = client
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
        if (reserves := item.get('reserves')) is not None:
            if reserves.get('asset0') is None or reserves.get('asset0') == 'None':
                reserves.pop('asset0', None)
            if reserves.get('asset1') is None or reserves.get('asset1') == 'None':
                reserves.pop('asset1', None)
            if len(reserves) < 2:
                item.pop('reserves', None)
    return data


async def get_pool_from_pair(pair_id: str, client: httpx.AsyncClient) -> dict[str, Any]:
    # query ReserveID($pair_id: String!) {
    #   dex_pair(where: {id: {_eq: $pair_id}}) {
    #     dex_pool {
    #       dex_pool_id
    #       lp_token_id
    #     }
    #   }
    # }
    # TODO: ensure dict and response['data']['dex_pair'][0]
    ...


# TODO: could be decimal
async def get_reserves_by_id(asset_pool: str) -> int:
    # asset_pool = asset_id:pool_id
    # query GetReserves($asset_pool: String!) {
    #   balanceHistory(limit: 1, order_by: {id: desc}, where: {assetAccount: {_eq: $asset_pool}}) {
    #     balance
    #   }
    # }
    ...


# TODO: could be decimal
async def get_reserves_by_lp(lp_token_id: str) -> int:
    # query GetReservesLP($lp_token_id: Int) {
    #   supplyHistory(order_by: {id: desc}, limit: 1, where: {assetId: {_eq: $lp_token_id}}) {
    #     supply
    #   }
    # }
    ...

async def add_reserves_to_events(data: Any, config: ProxyConfig, client: httpx.AsyncClient) -> Any:
    # TODO: add fallback with error printing and skiping reserves
    pairs = [e['pairId'] for e in data.get('events', [])]
    # NOTE: pair -> (asset0_id, asset1_id, pool_id, lp_token_id)
    pairs_dict = {}
    for pair in pairs:
        response = await get_pool_from_pair(pair, client)
        if response['data']['dex_pair']:
            pair_info = response['data']['dex_pair'][0]
            pairs_dict[pair] = (pair_info['dex_pool']['dex_pool_id'],
                                pair_info['dex_pool']['lp_token_id'])

    for event in data.get('events', []):
        pool_id, lp_token_id = pairs_dict.get(event['pairId'], (None, None))
        asset0_id, asset1_id = event.get('asset0In') or event.get('asset0Out'), event.get('asset1In') or event.get('asset1Out')

        event['reserves'] = {
            'asset0': get_reserves_by_id(f'{asset0_id}:{pool_id}') if asset0_id == lp_token_id else get_reserves_by_lp(asset0_id),
            'asset1': get_reserves_by_id(f'{asset1_id}:{pool_id}') if asset1_id == lp_token_id else get_reserves_by_lp(asset1_id),
        }


async def transform_events(data: bytes, config: ProxyConfig, client: httpx.AsyncClient) -> bytes:
    """Clean JSON data by removing None fields and returning bytes"""
    try:
        json_data = orjson.loads(data)
        cleaned_data = remove_none_fields(json_data)
        enriched_data = await add_reserves_to_events(cleaned_data, config, client)
        return json_dumps(enriched_data, None)
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
    response = await client.send(forwarded_request)

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
