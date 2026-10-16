-- ==============================================================================
-- Valence Database Security: Enable RLS Across Partitioned Tables
-- File: scripts/enable_rls.sql
-- Description:
--   Resolves Supabase Security Advisor "RLS Disabled in Public" CRITICAL warnings.
--   Enables Row Level Security across all parent tables and monthly partitions.
--
-- Safety & Workflow Guarantee:
--   Valence application workflows (GitHub Actions, Streamlit, Telemetry, Health Probe)
--   connect as the database owner ('postgres') via DATABASE_URL. The 'postgres' role
--   possesses the BYPASSRLS attribute, meaning all existing and future workflows
--   continue to operate with 100% full read/write access without interruption.
--
-- How to apply:
--   Copy and paste this script into your Supabase Dashboard -> SQL Editor and Run.
-- ==============================================================================

-- 1. Clean up any event triggers from previous attempts
DROP EVENT TRIGGER IF EXISTS trg_auto_enable_rls;
DROP FUNCTION IF EXISTS public.auto_enable_rls_on_new_table();

-- 2. Enable RLS on core parent tables and telemetry
ALTER TABLE IF EXISTS public.event_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.event_payloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.pipeline_runs ENABLE ROW LEVEL SECURITY;

-- 3. Enable RLS explicitly on all known child partitions
ALTER TABLE IF EXISTS public.event_signals_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.event_payloads_history ENABLE ROW LEVEL SECURITY;

ALTER TABLE IF EXISTS public.event_signals_2026_10 ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.event_payloads_2026_10 ENABLE ROW LEVEL SECURITY;

ALTER TABLE IF EXISTS public.event_signals_2026_11 ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.event_payloads_2026_11 ENABLE ROW LEVEL SECURITY;

ALTER TABLE IF EXISTS public.event_signals_2026_12 ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.event_payloads_2026_12 ENABLE ROW LEVEL SECURITY;

-- 4. Dynamic safeguard: enable RLS on any other partitions or legacy tables in public schema
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
          AND (
            tablename LIKE 'event_signals%' 
            OR tablename LIKE 'event_payloads%' 
            OR tablename = 'pipeline_runs'
          )
    ) LOOP
        EXECUTE 'ALTER TABLE public.' || quote_ident(r.tablename) || ' ENABLE ROW LEVEL SECURITY;';
        RAISE NOTICE 'Row Level Security verified on: public.%', r.tablename;
    END LOOP;
END $$;

-- 5. Verification Query: Confirm all tables and partitions show rowsecurity = true
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND (tablename LIKE 'event_signals%' OR tablename LIKE 'event_payloads%' OR tablename = 'pipeline_runs')
ORDER BY tablename;
