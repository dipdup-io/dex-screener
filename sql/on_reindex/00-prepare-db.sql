-- CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ALTER TABLE swap_event DROP CONSTRAINT swap_event_pkey;
-- ALTER TABLE swap_event ADD PRIMARY KEY (event_type, txn_id, txn_index, event_index);
-- SELECT create_hypertable('trade', 'timestamp');

-- ALTER TABLE join_exit_event DROP CONSTRAINT join_exit_event_pkey;
-- ALTER TABLE join_exit_event ADD PRIMARY KEY (event_type, txn_id, txn_index, event_index);

-- CREATE INDEX trade_exchange_id_idx ON public.trade USING btree (exchange_id, trader_id, timestamp);
