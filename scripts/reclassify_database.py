"""
Database Maintenance & Integrity CLI:
1. Regional Reclassification & Contaminant Purge (RegionalAffinityClassifier)
2. Historical Deduplication (NewsDeduplicator / canonical_fingerprint)
3. Historical Sentiment Re-Scoring (Grounded CLM-8B System-One Engine)

Usage:
    python scripts/reclassify_database.py --mode=dry-run
    python scripts/reclassify_database.py --mode=purge
    python scripts/reclassify_database.py --mode=dedup
    python scripts/reclassify_database.py --mode=rescore
    python scripts/reclassify_database.py --mode=full-clean
"""

import os
import sys
import argparse
import psycopg2

# Ensure src/ is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from ingestion.classifier import RegionalAffinityClassifier
from ingestion.dedup import canonical_fingerprint
from main import score_sentiment, load_okf_rules
from typesafe_sdk import TypeSafeClient

def delete_ids_in_batches(cur, ids_to_delete, batch_size=500):
    if not ids_to_delete:
        return 0, 0
    deleted_p = 0
    deleted_s = 0
    for i in range(0, len(ids_to_delete), batch_size):
        batch = [str(uid) for uid in ids_to_delete[i:i + batch_size]]
        cur.execute("DELETE FROM event_payloads WHERE id = ANY(%s::uuid[]);", (batch,))
        deleted_p += cur.rowcount
        cur.execute("DELETE FROM event_signals WHERE id = ANY(%s::uuid[]);", (batch,))
        deleted_s += cur.rowcount
    return deleted_p, deleted_s

def run_audit_and_purge(conn, classifier, do_purge=False):
    print("\n--- [STAGE 1] Regional Affinity & Contaminant Audit ---")
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
        print(f"Total historical records: {total_records}")

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

        print(f"  Verified authentic:        {valid_count} ({valid_count/max(1, total_records)*100:.1f}%)")
        print(f"  Contaminants detected:     {contaminant_count} ({contaminant_count/max(1, total_records)*100:.1f}%)")
        for r_code, count in sorted(contaminants_by_region.items()):
            print(f"    - {r_code}: {count} records")

        if do_purge and contaminant_ids:
            print(f"Purging {len(contaminant_ids)} contaminant records...")
            del_p, del_s = delete_ids_in_batches(cur, contaminant_ids)
            conn.commit()
            print(f"  Purge complete: {del_p} payloads, {del_s} signals deleted.")
        elif not do_purge:
            print("  (Dry-run: No contaminant rows deleted)")

    return contaminant_ids

def run_deduplication(conn, do_purge=False):
    print("\n--- [STAGE 2] Historical News Deduplication ---")
    with conn.cursor() as cur:
        query = """
            SELECT s.id, s.market_region, s.index_ticker, s.timestamp, p.raw_text
            FROM event_signals s
            JOIN event_payloads p ON s.id = p.id
            ORDER BY s.timestamp DESC;
        """
        cur.execute(query)
        rows = cur.fetchall()

        seen_fingerprints = {}
        duplicate_ids = []
        canonical_count = 0

        for row in rows:
            rec_id, region, ticker, ts, raw_text = row
            fp = canonical_fingerprint(str(raw_text or ""))
            if not fp:
                continue

            # Group by (region, fingerprint) so each region keeps 1 canonical report
            key = (region, fp)
            if key in seen_fingerprints:
                duplicate_ids.append(rec_id)
            else:
                seen_fingerprints[key] = rec_id
                canonical_count += 1

        print(f"  Total records scanned: {len(rows)}")
        print(f"  Unique distinct news:  {canonical_count}")
        print(f"  Redundant duplicates:  {len(duplicate_ids)} ({len(duplicate_ids)/max(1, len(rows))*100:.1f}%)")

        if do_purge and duplicate_ids:
            print(f"Purging {len(duplicate_ids)} redundant duplicate records...")
            del_p, del_s = delete_ids_in_batches(cur, duplicate_ids)
            conn.commit()
            print(f"  Deduplication purge complete: {del_p} payloads, {del_s} signals deleted.")
        elif not do_purge:
            print("  (Dry-run: No duplicate rows deleted)")

    return duplicate_ids

from config.market_registry import load_market_registry

def get_asset_class_for_ticker(region: str, ticker: str) -> str:
    registry = load_market_registry()
    r_meta = registry.get(region, {})
    for idx in r_meta.get("indices", []):
        if idx.get("ticker") == ticker:
            return idx.get("asset_class", "equity")
    return "equity"

def run_rescoring(conn, batch_limit=None):
    print("\n--- [STAGE 3] Grounded Sentiment Re-Scoring ---")
    typesafe_api_key = os.environ.get('TYPESAFE_API_KEY')
    client = TypeSafeClient(
        api_key=typesafe_api_key.strip() if typesafe_api_key else 'empty_key_allowed',
        base_url='https://shivam-jha96--clm-macro-engine-clm-server.modal.run',
        model='clm-latest',
        timeout=120.0
    )

    with conn.cursor() as cur:
        query = """
            SELECT s.id, s.market_region, s.index_ticker, s.sentiment_score, p.raw_text
            FROM event_signals s
            JOIN event_payloads p ON s.id = p.id
            ORDER BY s.timestamp DESC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        if batch_limit:
            rows = rows[:batch_limit]

        print(f"Re-scoring {len(rows)} authentic historical records via Grounded CLM...")
        updated_count = 0

        for row in rows:
            rec_id, region, ticker, old_score, raw_text = row
            asset_class = get_asset_class_for_ticker(region, ticker)
            context = load_okf_rules(region)
            res = score_sentiment(client, str(raw_text or ""), context, region_tag=region, asset_class=asset_class)
            new_score = float(res.get("DirectionalScore", 0.0))

            cur.execute("""
                UPDATE event_signals
                SET sentiment_score = %s
                WHERE id = %s;
            """, (new_score, rec_id))
            updated_count += 1

            if updated_count % 25 == 0 or updated_count == len(rows):
                conn.commit()
                print(f"  Processed & updated {updated_count}/{len(rows)} records...")

        conn.commit()
        print(f"Re-scoring complete: {updated_count} records updated with grounded sentiment.")

def main():
    parser = argparse.ArgumentParser(description="Database maintenance CLI for GSP.")
    parser.add_argument(
        "--mode",
        choices=["dry-run", "purge", "dedup", "rescore", "full-clean"],
        default="dry-run",
        help="Execution mode (default: dry-run)"
    )
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is missing.")
        sys.exit(1)

    print(f"=== Database Regional & Sentiment Maintenance CLI ===")
    print(f"Mode: {args.mode.upper()}")

    classifier = RegionalAffinityClassifier()
    conn = psycopg2.connect(db_url)

    try:
        if args.mode == "dry-run":
            run_audit_and_purge(conn, classifier, do_purge=False)
            run_deduplication(conn, do_purge=False)
        elif args.mode == "purge":
            run_audit_and_purge(conn, classifier, do_purge=True)
        elif args.mode == "dedup":
            run_deduplication(conn, do_purge=True)
        elif args.mode == "rescore":
            run_rescoring(conn)
        elif args.mode == "full-clean":
            run_audit_and_purge(conn, classifier, do_purge=True)
            run_deduplication(conn, do_purge=True)
            run_rescoring(conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
