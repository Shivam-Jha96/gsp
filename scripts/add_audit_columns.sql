-- Migration: Add point-in-time audit metadata columns to event_signals
-- Safe to run multiple times (idempotent)

ALTER TABLE event_signals ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;
ALTER TABLE event_signals ADD COLUMN IF NOT EXISTS scored_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE event_signals ADD COLUMN IF NOT EXISTS okf_version_hash VARCHAR(64);
ALTER TABLE event_signals ADD COLUMN IF NOT EXISTS model_version VARCHAR(64) DEFAULT 'clm-8b-v1';
