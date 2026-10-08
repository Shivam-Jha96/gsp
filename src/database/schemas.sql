-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The Math Layer
CREATE TABLE event_signals (
    id UUID DEFAULT uuid_generate_v4(),
    index_ticker VARCHAR(50) NOT NULL,
    market_region VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    sentiment_score NUMERIC,
    published_at TIMESTAMPTZ,
    scored_at TIMESTAMPTZ DEFAULT NOW(),
    okf_version_hash VARCHAR(64),
    model_version VARCHAR(64) DEFAULT 'clm-8b-v1',
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Composite B-Tree index on (index_ticker, timestamp DESC)
CREATE INDEX idx_event_signals_ticker_time ON event_signals USING btree (index_ticker, timestamp DESC);

-- BRIN index on the timestamp column
CREATE INDEX idx_event_signals_timestamp_brin ON event_signals USING brin (timestamp);

-- B-Tree index specifically for sorting the latest events dashboard view (UI Query)
CREATE INDEX idx_event_signals_time_desc ON event_signals USING btree (timestamp DESC);

-- The Document Layer (Vertical Partitioning via 1-to-1 relationship)
CREATE TABLE event_payloads (
    id UUID,
    timestamp TIMESTAMPTZ NOT NULL,
    raw_text TEXT,
    applied_okf_rules TEXT,
    metadata JSONB,
    fingerprint_hash VARCHAR(64),
    PRIMARY KEY (id, timestamp),
    FOREIGN KEY (id, timestamp) REFERENCES event_signals(id, timestamp) ON DELETE CASCADE
) PARTITION BY RANGE (timestamp);

-- Index for fast deduplication lookup
CREATE INDEX idx_event_payloads_fingerprint ON event_payloads (fingerprint_hash);

-- Default/Current Partitions (Automate creation for future months via cron or triggers)
CREATE TABLE event_signals_2026_10 PARTITION OF event_signals FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE event_payloads_2026_10 PARTITION OF event_payloads FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');


-- The Telemetry Layer: Tracks execution lifecycle & completion freshness of background pipelines
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'RUNNING', 'SUCCESS', 'FAILED'
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    duration_seconds NUMERIC(10, 2),
    items_polled INT DEFAULT 0,
    items_scored INT DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Index for instant lookup of latest successful pipeline execution
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_lookup 
ON pipeline_runs (pipeline_name, status, completed_at DESC);

