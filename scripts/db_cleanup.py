"""
One-time database maintenance script to purge records older than 12:00 PM IST on September 30, 2026.
12:00 PM IST (UTC+05:30) == 06:30 AM UTC on 2026-09-30.
"""
import os
import sys
import psycopg2

def run_cleanup():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is missing.")
        sys.exit(1)

    cutoff_utc = "2026-09-30 06:30:00+00"
    cutoff_ist = "2026-09-30 12:00:00+05:30"
    print(f"=== Database Maintenance: Purge data older than {cutoff_ist} ({cutoff_utc}) ===")

    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            # 1. Total counts before cleanup
            cur.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM event_signals;")
            total_signals, min_time, max_time = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM event_payloads;")
            total_payloads = cur.fetchone()[0]

            print("\n[BEFORE PURGE] Current Database Status:")
            print(f"  event_signals total:  {total_signals}")
            print(f"  event_payloads total: {total_payloads}")
            print(f"  Timestamp range:      {min_time} -> {max_time}")

            # 2. Counts to be deleted
            cur.execute("SELECT COUNT(*) FROM event_signals WHERE timestamp < %s;", (cutoff_utc,))
            to_delete_signals = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM event_payloads 
                WHERE id IN (SELECT id FROM event_signals WHERE timestamp < %s);
            """, (cutoff_utc,))
            to_delete_payloads = cur.fetchone()[0]

            print(f"\n[TARGET PURGE] Records older than {cutoff_ist}:")
            print(f"  event_signals to delete:  {to_delete_signals}")
            print(f"  event_payloads to delete: {to_delete_payloads}")

            # 3. Counts to be retained
            cur.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM event_signals WHERE timestamp >= %s;", (cutoff_utc,))
            to_keep_signals, keep_min_time, keep_max_time = cur.fetchone()
            print(f"\n[TARGET RETAIN] Records >= {cutoff_ist}:")
            print(f"  event_signals to retain:  {to_keep_signals}")
            print(f"  Retained timestamp range: {keep_min_time} -> {keep_max_time}")

            if to_delete_signals == 0 and to_delete_payloads == 0:
                print("\nNo records found older than cutoff timestamp. Nothing to delete.")
                return

            # 4. Perform Deletion
            print("\n[EXECUTING] Deleting legacy records...")
            cur.execute("""
                DELETE FROM event_payloads 
                WHERE id IN (SELECT id FROM event_signals WHERE timestamp < %s);
            """, (cutoff_utc,))
            deleted_p = cur.rowcount
            print(f"  Deleted {deleted_p} rows from event_payloads.")

            cur.execute("DELETE FROM event_signals WHERE timestamp < %s;", (cutoff_utc,))
            deleted_s = cur.rowcount
            print(f"  Deleted {deleted_s} rows from event_signals.")

            conn.commit()
            print("Transaction committed successfully.")

            # 5. Verification
            cur.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM event_signals;")
            new_total_signals, new_min_time, new_max_time = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM event_payloads;")
            new_total_payloads = cur.fetchone()[0]

            print(f"\n[AFTER PURGE] Verified Status Post-Cleanup:")
            print(f"  event_signals remaining:  {new_total_signals}")
            print(f"  event_payloads remaining: {new_total_payloads}")
            print(f"  New timestamp range:      {new_min_time} -> {new_max_time}")

    finally:
        conn.close()

if __name__ == "__main__":
    run_cleanup()
