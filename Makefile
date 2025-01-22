.PHONY: $(MAKECMDGOALS)
MAKEFLAGS += --no-print-directory
##
##  🚧 DipDup developer tools
##
PACKAGE=dex_screener
TAG=latest
COMPOSE=deploy/compose.yaml
CONFIG=sqlite

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

up:             ## Start Compose stack
	docker-compose -f ${COMPOSE} up -d --build
	docker-compose -f ${COMPOSE} logs -f

down:           ## Stop Compose stack
	docker-compose -f ${COMPOSE} down

##

init_env:
	SQLITE_PATH=/tmp/dex_screener_hydration.sqlite dipdup -C hydration -C ${CONFIG} config env -o hydration.env --unsafe
	SQLITE_PATH=/tmp/dex_screener_assethub.sqlite dipdup -C assethub -C ${CONFIG} config env -o assethub.env --unsafe

init:
	dipdup -e hydration.env -C hydration -C ${CONFIG} init -f
	dipdup -e assethub.env -C assethub -C ${CONFIG} init -f
	make all

run_hydration:
	dipdup -e hydration.env -C hydration -C ${CONFIG} run

run_assethub:
	dipdup -e assethub.env -C assethub -C ${CONFIG} run

wipe_hydration:
	dipdup -e hydration.env -C hydration -C ${CONFIG} schema wipe

wipe_assethub:
	dipdup -e assethub.env -C assethub -C ${CONFIG} schema wipe
