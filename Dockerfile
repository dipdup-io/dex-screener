ARG PYTHON_VERSION=3.12-slim-bookworm
ARG SOURCE_DIR=dex_screener
ARG APP_PATH=/opt/app
ARG VENV_PATH=/.venv
ARG APP_USER=dipdup

FROM python:${PYTHON_VERSION} AS builder-base

ARG VENV_PATH
ENV VIRTUAL_ENV=$VENV_PATH

SHELL ["/bin/bash", "-c"]
RUN apt-get update \
 && apt-get install --no-install-recommends -y \
        # deps for building python deps
        build-essential \
    	git \
    \
    # cleanup
 && rm -rf /tmp/* \
 && rm -rf /root/.cache \
 && rm -rf /var/lib/apt/lists/*


FROM builder-base AS builder-production

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
	--mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
	uv sync --frozen --exact --no-install-project --no-editable --no-dev --no-installer-metadata \
    --no-install-package=sympy --no-install-package=cytoolz \
    --compile-bytecode \
    && for i in `find "${VENV_PATH}/lib" -wholename '*/__pycache__/*'`; do \
    cbn=`basename $i`; fn=${cbn:0:-16}; bn="${fn}.py"; cdn=`dirname $i`; dn=`dirname $cdn`; \
    echo "${dn}/${bn}"; mv $i "${dn}/${bn}c"; rm "${dn}/${bn}"; done \
    && find "${VENV_PATH}/lib" -type d -name '__pycache__' -print | xargs rm -d


FROM python:${PYTHON_VERSION} AS runtime-base

ARG VENV_PATH
ENV PATH=$VENV_PATH/bin:$PATH

ARG APP_PATH
WORKDIR $APP_PATH

ARG APP_USER
RUN useradd -ms /bin/bash $APP_USER


FROM runtime-base AS runtime

ARG VENV_PATH
COPY --from=builder-production ["$VENV_PATH", "$VENV_PATH"]

ARG APP_USER
USER $APP_USER
ARG SOURCE_DIR
ENV DIPDUP_PACKAGE_PATH=$APP_PATH/$SOURCE_DIR
COPY --chown=$APP_USER $SOURCE_DIR ./$SOURCE_DIR

ENTRYPOINT ["dipdup"]
CMD ["run"]
