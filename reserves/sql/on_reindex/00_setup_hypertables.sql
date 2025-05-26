CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;


ALTER TABLE balance_update_event
    DROP CONSTRAINT balance_update_event_pkey;
CREATE UNIQUE INDEX balance_update_event_pkey
    ON balance_update_event USING btree (id ASC);
ALTER TABLE balance_update_event
    ADD PRIMARY KEY USING INDEX balance_update_event_pkey;
CREATE INDEX idx_balance_update_event_asset_account
    ON balance_update_event USING hash (asset_account);
CREATE INDEX idx_balance_update_event_asset_id
    ON balance_update_event USING hash (asset_id);

SELECT create_hypertable('balance_update_event', 'id', if_not_exists := TRUE);
SELECT set_chunk_time_interval('balance_update_event', 100000::BIGINT << 17);


ALTER TABLE balance_history
    DROP CONSTRAINT balance_history_pkey;
CREATE UNIQUE INDEX balance_history_pkey
    ON balance_history USING btree (id ASC);
ALTER TABLE balance_history
    ADD PRIMARY KEY USING INDEX balance_history_pkey;
CREATE INDEX idx_balance_history_distinct
    ON balance_history USING btree (asset_account, id DESC);
CREATE INDEX idx_balance_history_asset_account
    ON balance_history USING hash (asset_account);
create index idx_balance_history_asset_account_btree
    on balance_history USING btree (asset_account);
CREATE INDEX idx_balance_history_asset_id
    ON balance_history USING hash (asset_id);

SELECT create_hypertable('balance_history', 'id', if_not_exists := TRUE);
SELECT set_chunk_time_interval('balance_history', 100000::BIGINT << 17);


ALTER TABLE supply_history
    DROP CONSTRAINT supply_history_pkey;
CREATE UNIQUE INDEX supply_history_pkey
    ON supply_history USING btree (id ASC);
ALTER TABLE supply_history
    ADD PRIMARY KEY USING INDEX supply_history_pkey;
CREATE INDEX idx_supply_history_distinct
    ON supply_history USING btree (asset_id, id DESC);
CREATE INDEX idx_supply_history_asset_id
    ON supply_history USING hash (asset_id);

SELECT create_hypertable('supply_history', 'id', if_not_exists := TRUE);
SELECT set_chunk_time_interval('supply_history', 100000::BIGINT << 18);
