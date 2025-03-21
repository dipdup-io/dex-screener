.PHONY: $(MAKECMDGOALS)
MAKEFLAGS += --no-print-directory
##
##  🚧 DipDup developer tools
##
PACKAGE=dex-screener
TAG=dev
COMPOSE=compose.yaml

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
