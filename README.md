# dex_screener

A blockchain indexer built with DipDup

## Installation

This project is based on [DipDup](https://dipdup.io), a framework for building featureful dapps.

You need a Linux/macOS system with Python 3.12 installed. To install DipDup with pipx or use our installer:

```shell
curl -Lsf https://dipdup.io/install.py | python3.12
```

See the [Installation](https://dipdup.io/docs/installation) page for all options.

## Usage

Run the indexer in Compose stack with PostgreSQL and Hasura:

```shell
cp .env.default .env
# Edit .env file before running
docker compose up -d
```

## Development setup

To set up the development environment:

```shell
make install
source .venv/bin/activate
```
