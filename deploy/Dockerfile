# FROM dipdup/dipdup:8
# FROM ghcr.io/dipdup-io/dipdup:8
FROM ghcr.io/dipdup-io/dipdup:fix-subsquid-substrate-dicts

# COPY --chown=dipdup pyproject.toml README.md .
# RUN pip install .

COPY --chown=dipdup . dex_screener
WORKDIR dex_screener