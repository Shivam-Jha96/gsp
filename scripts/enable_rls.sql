-- ==============================================================================
-- Valence Database Security Migration: Enable RLS & Auto-Protect Partitions
-- File: scripts/enable_rls.sql
-- Description:
--   Resolves Supabase Security Advisor "RLS Disabled in Public" CRITICAL warnings.
--   Enables Row Level Security across all core tables and monthly partitions.
--   Installs an event trigger to automatically enable RLS on any future partition.
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

-- 1. Enable RLS on core tables if they exist
ALTER TABLE IF EXISTS public.event_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.event_payloads ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.pipeline_runs ENABLE ROW LEVEL SECURITY;

-- 2. Dynamically enable RLS on all existing partitions and matching public tables
DO $$
DECLARE
    tbl RECORD;
BEGIN
    FOR tbl IN
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
          AND (
            tablename LIKE 'event_signals%' 
            OR tablename LIKE 'event_payloads%' 
            OR tablename = 'pipeline_runs'
          )
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', tbl.tablename);
        RAISE NOTICE 'Row Level Security successfully enabled on: public.%', tbl.tablename;
    END LOOP;
END $$;

-- 3. Lock down PostgREST HTTP Data API: Revoke public access from anon and authenticated roles
-- This ensures unauthenticated/anon web traffic hitting Supabase PostgREST endpoints cannot read/write tables.
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM anon, authenticated;

-- Ensure default privileges for future objects created in public do not grant access to anon/authenticated
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON ROUTINES FROM anon, authenticated;

-- 4. Automatically enable RLS on all future tables and partitions created in schema public
-- Whenever new monthly partitions (e.g. event_signals_2027_01) are created, this trigger ensures RLS is active.
CREATE OR REPLACE FUNCTION public.auto_enable_rls_on_new_table()
RETURNS event_trigger AS $$
DECLARE
    obj record;
BEGIN
    FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands() WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS')
    LOOP
        IF obj.schema_name = 'public' THEN
            EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY;', obj.object_identity);
            RAISE NOTICE 'Auto-enabled Row Level Security on newly created table: %', obj.object_identity;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Re-create the event trigger cleanly
DROP EVENT TRIGGER IF EXISTS trg_auto_enable_rls;
CREATE EVENT TRIGGER trg_auto_enable_rls
ON ddl_command_end
WHEN TAG IN ('CREATE TABLE', 'CREATE TABLE AS')
EXECUTE FUNCTION public.auto_enable_rls_on_new_table();

-- Verification Query: Check that all public event tables have rowsecurity = true
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND (tablename LIKE 'event_signals%' OR tablename LIKE 'event_payloads%' OR tablename = 'pipeline_runs')
ORDER BY tablename;
