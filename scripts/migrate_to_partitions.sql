-- Migration script to partition event_signals and event_payloads by month
-- RUN THIS IN YOUR SUPABASE SQL EDITOR

-- 0. Bulletproof Setup: Ensure real data is safely in _old tables, and clean up any failed new tables
DO $$
BEGIN
    -- If the _old tables don't exist, rename the current ones to _old
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'event_signals_old') THEN
        ALTER TABLE IF EXISTS event_signals RENAME TO event_signals_old;
    ELSE
        -- If _old exists AND current exists, the current is a leftover from a failed run. Drop it.
        IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'event_signals') THEN
            DROP TABLE event_signals CASCADE;
        END IF;
    END IF;

    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'event_payloads_old') THEN
        ALTER TABLE IF EXISTS event_payloads RENAME TO event_payloads_old;
    ELSE
        IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'event_payloads') THEN
            DROP TABLE event_payloads CASCADE;
        END IF;
    END IF;
END $$;

-- 1. Rename indexes on the old tables so their names can be reused
ALTER INDEX IF EXISTS idx_event_signals_ticker_time RENAME TO idx_event_signals_ticker_time_old;
ALTER INDEX IF EXISTS idx_event_signals_timestamp_brin RENAME TO idx_event_signals_timestamp_brin_old;
ALTER INDEX IF EXISTS idx_event_signals_time_desc RENAME TO idx_event_signals_time_desc_old;
ALTER INDEX IF EXISTS idx_event_payloads_fingerprint RENAME TO idx_event_payloads_fingerprint_old;


-- 2. Create the new Partitioned 'event_signals' (Math Layer)
CREATE TABLE event_signals (
    id UUID DEFAULT uuid_generate_v4(),
    index_ticker VARCHAR(50) NOT NULL,
    market_region VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    sentiment_score NUMERIC,
    -- Partitioned tables require the partition key in the Primary Key
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Re-create indices for the partitioned table
CREATE INDEX idx_event_signals_ticker_time ON event_signals USING btree (index_ticker, timestamp DESC);
CREATE INDEX idx_event_signals_time_desc ON event_signals USING btree (timestamp DESC);
CREATE INDEX idx_event_signals_timestamp_brin ON event_signals USING brin (timestamp);

-- 3. Create the new Partitioned 'event_payloads' (Document Layer)
CREATE TABLE event_payloads (
    id UUID,
    timestamp TIMESTAMPTZ NOT NULL, -- Added to enable partitioning
    raw_text TEXT,
    applied_okf_rules TEXT,
    metadata JSONB,
    fingerprint_hash VARCHAR(64),
    PRIMARY KEY (id, timestamp),
    FOREIGN KEY (id, timestamp) REFERENCES event_signals(id, timestamp) ON DELETE CASCADE
) PARTITION BY RANGE (timestamp);

-- Re-create fingerprint index
CREATE INDEX idx_event_payloads_fingerprint ON event_payloads (fingerprint_hash);

-- 4. Create Partitions for Past Data and Upcoming Months
-- Catch-all for historical data up to Sept 2026
CREATE TABLE event_signals_history PARTITION OF event_signals FOR VALUES FROM ('2000-01-01') TO ('2026-10-01');
CREATE TABLE event_payloads_history PARTITION OF event_payloads FOR VALUES FROM ('2000-01-01') TO ('2026-10-01');

-- October 2026
CREATE TABLE event_signals_2026_10 PARTITION OF event_signals FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE event_payloads_2026_10 PARTITION OF event_payloads FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

-- November 2026
CREATE TABLE event_signals_2026_11 PARTITION OF event_signals FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE event_payloads_2026_11 PARTITION OF event_payloads FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');

-- December 2026
CREATE TABLE event_signals_2026_12 PARTITION OF event_signals FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
CREATE TABLE event_payloads_2026_12 PARTITION OF event_payloads FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');


-- 5. Migrate Data from Old Tables to New Partitioned Tables
INSERT INTO event_signals (id, index_ticker, market_region, timestamp, sentiment_score)
SELECT id, index_ticker, market_region, timestamp, sentiment_score FROM event_signals_old;

INSERT INTO event_payloads (id, timestamp, raw_text, applied_okf_rules, metadata, fingerprint_hash)
SELECT p.id, s.timestamp, p.raw_text, p.applied_okf_rules, p.metadata, NULL
FROM event_payloads_old p
JOIN event_signals_old s ON p.id = s.id;

-- NOTE: Once you verify that all data appears in the app correctly, you can drop the old tables:
-- DROP TABLE event_payloads_old;
-- DROP TABLE event_signals_old;
