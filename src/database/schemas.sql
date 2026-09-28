-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The Math Layer
CREATE TABLE event_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    index_ticker VARCHAR(50) NOT NULL,
    market_region VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    sentiment_score NUMERIC
);

-- Composite B-Tree index on (index_ticker, timestamp DESC)
CREATE INDEX idx_event_signals_ticker_time ON event_signals USING btree (index_ticker, timestamp DESC);

-- BRIN index on the timestamp column
CREATE INDEX idx_event_signals_timestamp_brin ON event_signals USING brin (timestamp);

-- The Document Layer (Vertical Partitioning via 1-to-1 relationship)
CREATE TABLE event_payloads (
    id UUID PRIMARY KEY REFERENCES event_signals(id) ON DELETE CASCADE,
    raw_text TEXT,
    applied_okf_rules TEXT[],
    metadata JSONB
);
