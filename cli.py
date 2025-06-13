import logging
from typing import TYPE_CHECKING

import click
from dipdup.cli import _cli_wrapper
from dipdup.cli import cli

if TYPE_CHECKING:
    from dipdup.config import DipDupConfig


@cli.command(help='Run API proxy server')
@click.pass_context
@_cli_wrapper
async def proxy(ctx) -> None:
    import uvicorn
    from dipdup.env import DEBUG

    from dex_screener.proxy import ProxyConfig
    from dex_screener.proxy import create_api

    config: DipDupConfig = ctx.obj.config

    proxy_config = ProxyConfig(config.custom['proxy'])

    api = create_api(proxy_config)

    uv_config = uvicorn.Config(
        app=api,
        host=proxy_config.server_host,
        port=int(proxy_config.server_port),
        log_config={'version': 1, 'disable_existing_loggers': False},
    )
    logging.getLogger('uvicorn').setLevel(logging.DEBUG if DEBUG else logging.INFO)
    server = uvicorn.Server(uv_config)
    await server.serve()
