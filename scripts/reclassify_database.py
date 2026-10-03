"""
Database Maintenance Script:
Runs RegionalAffinityClassifier on all historical database records in Supabase
to detect and eliminate cross-region contaminants and non-market noise.

Usage:
    python scripts/reclassify_database.py --mode=dry-run
    python scripts/reclassify_database.py --mode=purge
"""

import os
import sys
import argparse
import psycopg2

# Ensure src/ is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from ingestion.classifier import RegionalAffinityClassifier

def reclassify_database(mode: str = "dry-run"):
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is missing.")
        sys.exit(1)

    print(f"=== Database Regional Reclassification & Contaminant Audit ===")
    print(f"Mode: {mode.upper()}")

    classifier = RegionalAffinityClassifier()
    conn = psycopg2.connect(db_url)

    try:
        with conn.cursor() as cur:
            query = """
                SELECT s.id, s.market_region, s.index_ticker, s.timestamp, p.raw_text
                FROM event_signals s
                JOIN event_payloads p ON s.id = p.id
                ORDER BY s.timestamp DESC;
            """
            cur.execute(query)
            rows = cur.fetchall()

            total_records = len(rows)
            print(f"\nFetched {total_records} total historical records from Supabase.")

            valid_count = 0
            contaminant_count = 0
            contaminant_ids = []
            contaminants_by_region = {}

            for row in rows:
                rec_id, region, ticker, ts, raw_text = row
                res = classifier.classify_and_validate(
                    headline=str(raw_text or ""),
                    summary="",
                    expected_region=region,
                    expected_ticker=ticker,
                    allow_reroute=False
                )

                if res is not None:
                    valid_count += 1
                else:
                    contaminant_count += 1
                    contaminant_ids.append(rec_id)
                    contaminants_by_region[region] = contaminants_by_region.get(region, 0) + 1
                    if len(contaminant_ids) <= 10:
                        clean_text = str(raw_text or "").replace("\n", " ")[:70]
                        print(f"  [CONTAMINANT #{contaminant_count}] [{region}] {ticker}: {clean_text}...")

            print("\n" + "="*50)
            print("AUDIT SUMMARY:")
            print(f"  Total records scanned:     {total_records}")
            print(f"  Verified authentic:        {valid_count} ({valid_count/max(1, total_records)*100:.1f}%)")
            print(f"  Misclassified/Contaminant: {contaminant_count} ({contaminant_count/max(1, total_records)*100:.1f}%)")
            print("  Contaminants breakdown by tagged region:")
            for r_code, count in sorted(contaminants_by_region.items()):
                print(f"    - {r_code}: {count} records")
            print("="*50)

            if mode == "purge":
                if not contaminant_ids:
                    print("\nNo contaminants found. Nothing to purge.")
                    return

                print(f"\n[PURGING] Deleting {len(contaminant_ids)} contaminated records from Supabase...")
                batch_size = 500
                deleted_p = 0
                deleted_s = 0
                for i in range(0, len(contaminant_ids), batch_size):
                    batch = [str(uid) for uid in contaminant_ids[i:i + batch_size]]
                    # Delete from payloads first
                    cur.execute(
                        "DELETE FROM event_payloads WHERE id = ANY(%s::uuid[]);",
                        (batch,)
                    )
                    deleted_p += cur.rowcount

                    # Delete from signals
                    cur.execute(
                        "DELETE FROM event_signals WHERE id = ANY(%s::uuid[]);",
                        (batch,)
                    )
                    deleted_s += cur.rowcount

                print(f"  Deleted {deleted_p} rows from event_payloads.")
                print(f"  Deleted {deleted_s} rows from event_signals.")

                conn.commit()
                print("Purge transaction committed successfully!")
            else:
                print("\n[DRY RUN COMPLETE] To permanently remove these contaminants, run with --mode=purge.")

    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reclassify and audit database records for regional contamination.")
    parser.add_argument("--mode", choices=["dry-run", "purge"], default="dry-run", help="Execution mode (default: dry-run)")
    args = parser.parse_args()
    reclassify_database(mode=args.mode)
