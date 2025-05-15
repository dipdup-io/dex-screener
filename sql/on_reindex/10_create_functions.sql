CREATE FUNCTION event_id(event_row dex_event)
RETURNS TEXT AS $$
  SELECT event_row.block_id || '-' || event_row.event_index
$$ LANGUAGE sql STABLE;

CREATE FUNCTION tx_id(event_row dex_event)
RETURNS TEXT AS $$
  SELECT event_row.block_id || '-' || event_row.tx_index
$$ LANGUAGE sql STABLE;

CREATE FUNCTION pair_tx_id(pair_row dex_pair)
RETURNS TEXT AS $$
  SELECT pair_row.created_at_block_id || '-' || pair_row.created_at_tx_id
$$ LANGUAGE sql STABLE;
