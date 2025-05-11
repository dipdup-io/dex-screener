CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

SELECT create_hypertable('balance_update_event', 'id', if_not_exists:=TRUE);
SELECT set_chunk_time_interval('balance_update_event', 50000::BIGINT<<17);

SELECT create_hypertable('balance_history', 'id', if_not_exists:=TRUE);
SELECT set_chunk_time_interval('balance_history', 50000::BIGINT<<17);

SELECT create_hypertable('supply_history', 'id', if_not_exists:=TRUE);
SELECT set_chunk_time_interval('supply_history', 50000::BIGINT<<18);
