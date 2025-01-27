.PHONY: $(MAKECMDGOALS)
MAKEFLAGS += --no-print-directory
##
##  🚧 DipDup developer tools
##
PACKAGE=dex_screener
TAG=latest
COMPOSE=deploy/compose.yaml

help:           ## Show this help (default)
	@grep -Fh "##" $(MAKEFILE_LIST) | grep -Fv grep -F | sed -e 's/\\$$//' | sed -e 's/##//'

all:            ## Run an entire CI pipeline
	make format lint

##

install:        ## Install dependencies
	uv sync --all-extras --all-groups

update:         ## Update dependencies
	dipdup self update -q
	uv sync --all-extras --all-groups

format:         ## Format with all tools
	make black

lint:           ## Lint with all tools
	make ruff mypy

##

black:          ## Format with black
	black .

ruff:           ## Lint with ruff
	ruff check --fix .

mypy:           ## Lint with mypy
	mypy .

##

image:          ## Build Docker image
	docker buildx build . -t ${PACKAGE}:${TAG} --load

up:             ## Start Compose stacks
	PROJECT=hydration docker-compose -p hydration -f ${COMPOSE} --env-file hydration.compose.env up -d --build
	PROJECT=assethub docker-compose -p assethub -f ${COMPOSE} --env-file assethub.compose.env up -d --build

down:           ## Stop Compose stacks
	docker-compose -p hydration -f ${COMPOSE} down
	docker-compose -p assethub -f ${COMPOSE} down

##

# NOTE: Export env vars for datasources before running this command
init_env:       ## Create .env files to run indexers
	SQLITE_PATH=/tmp/dex_screener_hydration.sqlite dipdup -C hydration -C sqlite config env -o hydration.env --unsafe
	SQLITE_PATH=/tmp/dex_screener_assethub.sqlite dipdup -C assethub -C sqlite config env -o assethub.env --unsafe
	POSTGRES_PASSWORD=test HASURA_SECRET=test dipdup -C hydration -C compose config env -o hydration.compose.env --unsafe
	POSTGRES_PASSWORD=test HASURA_SECRET=test dipdup -C assethub -C compose config env -o assethub.compose.env --unsafe

init:           ## Initialize indexer
	dipdup -e hydration.env -C hydration -C sqlite init -f
	dipdup -e assethub.env -C assethub -C sqlite init -f
	make all

run_assethub:   ## Run AssetHub indexer in sqlite
	dipdup -e assethub.env -C assethub -C sqlite run

run_hydration:  ## Run Hydration indexer in sqlite
	dipdup -e hydration.env -C hydration -C sqlite run

wipe_assethub:  ## Wipe AssetHub indexer schema
	dipdup -e assethub.env -C assethub -C sqlite schema wipe

wipe_hydration: ## Wipe Hydration indexer schema
	dipdup -e hydration.env -C hydration -C sqlite schema wipe
