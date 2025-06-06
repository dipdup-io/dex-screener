#!/usr/bin/env python3

import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any

import httpx
import orjson
from dipdup.utils import json_dumps
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import Response
from starlette.background import BackgroundTask

"""
Environment variables:
- HTTP_CLIENT_HOST: Host of the HTTP client (default: hasura)
- HTTP_CLIENT_PORT: Port of the HTTP client (default: 8080)
- HTTP_SERVER_URL_PATH: URL path prefix for the API (default: /api/rest)
- HTTP_SERVER_HOST: Host for the FastAPI server (default: 0.0.0.0)
- HTTP_SERVER_PORT: Port for the FastAPI server (default: 8000)
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage HTTP client lifecycle"""
    # TODO: add http client to state(async with yeild {client: cl}), add env variables with client host and port
    client_host = os.getenv('HTTP_CLIENT_HOST', 'hasura')
    client_port = os.getenv('HTTP_CLIENT_PORT', '8080')
    async with httpx.AsyncClient(base_url=f'http://{client_host}:{client_port}') as client:
        yield {'client': client}


app = FastAPI(lifespan=lifespan)
base_route = APIRouter(prefix=os.getenv('HTTP_SERVER_URL_PATH', '/api/rest'))


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
            if len(reserves) == 0:
                item.pop('reserves', None)
    return data


def clean_json(data: Any) -> Any:
    try:
        json_data = orjson.loads(data)
        cleaned_data = remove_none_fields(json_data)
        return json_dumps(cleaned_data, None)
    except orjson.JSONDecodeError as e:
        print('Failed to decode JSON content: ', e)
        return data
    except Exception as e:
        print('Error processing data: ', e)
        return data


async def forward_request(request: Request, transform: Callable[[bytes], bytes] | None = None) -> Response:
    # Forward request with exact headers and body
    client: httpx.AsyncClient = request.state.client
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
    print(f'Forwarding request to {forwarded_request.url}')
    response = await client.send(forwarded_request, stream=True)

    if transform:
        # Read JSON content
        content = await response.aread()
        data = transform(content)
        response.headers['Content-Length'] = str(len(data)) if data else '0'
        return Response(
            data, status_code=response.status_code, headers=response.headers, background=BackgroundTask(response.aclose)
        )

    return Response(
        await response.aread(),
        status_code=response.status_code,
        headers=response.headers,
        background=BackgroundTask(response.aclose),
    )


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


if __name__ == '__main__':
    import uvicorn

    app.include_router(base_route)

    server_host = os.getenv('HTTP_SERVER_HOST', '0.0.0.0')
    server_port = int(os.getenv('HTTP_SERVER_PORT', 8000))
    uvicorn.run(app, host=server_host, port=server_port)
