CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

SELECT public.create_hypertable('dex_event', 'id', if_not_exists:=TRUE);
SELECT public.set_chunk_time_interval('dex_event', 100000);


-- see: https://github.com/tortoise/tortoise-orm/issues/1428
ALTER TABLE dex_event DROP CONSTRAINT dex_event_pair_id_fkey;
ALTER TABLE dex_event ADD FOREIGN KEY (pair_id) REFERENCES dex_pair
        ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE dex_pair DROP CONSTRAINT dex_pair_pool_id_fkey;
ALTER TABLE dex_pair ADD FOREIGN KEY (pool_id) REFERENCES dex_pool
        ON UPDATE CASCADE ON DELETE CASCADE;
