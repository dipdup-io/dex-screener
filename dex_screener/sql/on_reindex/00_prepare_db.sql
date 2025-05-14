CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

SELECT create_hypertable('dex_event', 'id', if_not_exists:=TRUE);
SELECT set_chunk_time_interval('dex_event', 100000);
