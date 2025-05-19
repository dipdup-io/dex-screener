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
CREATE INDEX idx_supply_history_asset_id
    ON supply_history USING hash (asset_id);

SELECT create_hypertable('supply_history', 'id', if_not_exists := TRUE);
SELECT set_chunk_time_interval('supply_history', 100000::BIGINT << 18);


alter table balance_update_event
set access method hypercore;
alter table balance_update_event
set (
    timescaledb.orderby = 'id',
    timescaledb.segmentby = 'asset_account'
);

alter table balance_history
set access method hypercore;
alter table balance_history
set (
    timescaledb.orderby = 'id',
    timescaledb.segmentby = 'asset_account'
);

alter table supply_history
set access method hypercore;
alter table supply_history
set (
    timescaledb.orderby = 'id',
    timescaledb.segmentby = 'asset_id'
);

CALL add_columnstore_policy('balance_update_event', after => 100000::BIGINT<<17-2);
CALL add_columnstore_policy('balance_history', after => 100000::BIGINT<<17-2);
CALL add_columnstore_policy('supply_history', after => 100000::BIGINT<<18-2);
