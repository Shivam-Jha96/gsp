import asyncio
import logging
import os
import json
import uuid

# Ingestion
from ingestion.poller import FeedPoller, FEEDS
from ingestion.dedup import canonical_fingerprint

# AI Engine (TypeSafe AI - Jev System-One Model)
from typesafe_sdk import TypeSafeClient, Choice

from config.market_registry import get_region_meta, load_asset_classes

def score_sentiment(client, text: str, region_context: str = "", region_tag: str = "GLOBAL", asset_class: str = "equity") -> dict:
    """
    Sends the target financial news event to TypeSafe AI's Jev model using the official SDK.
    Grounds choices in asset-class aware bipolar criteria (Bullish vs Bearish)
    to eliminate inverse bias for non-equity assets.
    Produces a continuous, calibrated directional score in [-1.0, 1.0].
    """
    try:
        all_classes = load_asset_classes()
        criteria = all_classes.get(asset_class, all_classes.get("equity", {}))
        
        # Keep state focused on the target financial event to prevent context dilution
        formatted_asset_class = asset_class.replace('_', ' ').title()
        state_content = f"Target Financial News Event ({region_tag} Market - {formatted_asset_class} Asset Class):\n{text}"

        # Jev evaluates states via explicitly grounded bipolar Choices
        result = client.system_one(
            state=state_content,
            questions={
                "direction": Choice(
                    instructions=f"Directional sentiment of this financial news event concerning the {formatted_asset_class} market:",
                    criteria=criteria
                )
            }
        )
        
        # Extract the structured decisions natively
        choice_obj = result.choices["direction"]
        probs = choice_obj.probabilities or {}
        
        p_bull = float(probs.get("Bullish", 0.0))
        p_bear = float(probs.get("Bearish", 0.0))
        p_neut = float(probs.get("Neutral", 0.0))
        
        # Normalize in case they don't sum to 1 (TypeSafe Jev usually does, but safe fallback)
        total_p = p_bull + p_bear + p_neut
        if total_p > 0:
            p_bull /= total_p
            p_bear /= total_p
            p_neut /= total_p
        
        # Relative Directional Spread: S_rel
        spread_denom = p_bull + p_bear + 1e-9
        s_rel = (p_bull - p_bear) / spread_denom
        
        # Conviction Magnitude weighted by Neutral attenuation: M
        magnitude = abs(s_rel) * (1.0 - 0.5 * p_neut)
        
        # Signed directional score [-1.0, 1.0]
        if s_rel > 0:
            directional_score = magnitude
        else:
            directional_score = -magnitude
            
        # Categorical label assignment
        if abs(directional_score) < 0.05 or p_neut > max(p_bull, p_bear):
            choice_str = "Neutral"
        elif directional_score > 0:
            choice_str = "Bullish"
        else:
            choice_str = "Bearish"
            
        # Clamp to [-1.0, 1.0]
        directional_score = max(-1.0, min(1.0, directional_score))
        score_magnitude = abs(directional_score)
        
        return {
            "Choice": choice_str,
            "Score": score_magnitude,
            "DirectionalScore": directional_score,
            "Probabilities": probs,
            "Noul": f"Evaluated via TypeSafe Jev (P_bull={p_bull:.2f}, P_bear={p_bear:.2f})"
        }
        
    except Exception as e:
        logging.error(f"Failed to reach TypeSafe API: {e}")
        return {"Choice": "Neutral", "Score": 0.0, "DirectionalScore": 0.0, "Noul": f"API Error: {e}"}

# Database
from database.client import get_db_client
from database.telemetry import track_pipeline_run

# Signal Engine
from signal_engine.cron_jobs import cron_ema_trigger

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)



def load_okf_rules(region_tag: str) -> str:
    """Loads the regional OKF markdown rules dynamically based on the market registry."""
    meta = get_region_meta(region_tag)
    if not meta or not meta.get("okf_file"):
        return "No specific macro rules for this region."
        
    rel_path = meta["okf_file"]
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), rel_path)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Knowledge file {filepath} not found.")
        return "No specific macro rules for this region."

async def run_ingestion_pipeline():
    """
    Step 1: Poll global feeds
    Step 2: Score sentiment via AI Engine
    Step 3: Insert into Database
    """
    logger.info("--- Starting Ingestion Pipeline ---")
    
    # 1. Poll Feeds
    poller = FeedPoller(feeds=FEEDS)
    payloads = await poller.run()
    
    if not payloads:
        logger.info("No new payloads fetched.")
        return 0, 0

    # Connect to the custom serverless Modal deployment running Contrastive-LM
    typesafe_api_key = os.environ.get('TYPESAFE_API_KEY')
    client = TypeSafeClient(api_key=typesafe_api_key.strip() if typesafe_api_key else 'empty_key_allowed', base_url='https://shivam-jha96--clm-macro-engine-clm-server.modal.run', model='clm-latest', timeout=120.0)

    # Initialize DB (Requires DATABASE_URL environment variable)
    db_client = None
    existing_fingerprints = set()
    if os.environ.get("DATABASE_URL"):
        try:
            db_client = get_db_client()
            with db_client.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT p.fingerprint_hash, p.raw_text
                        FROM event_payloads p
                        JOIN event_signals s ON p.id = s.id
                        WHERE s.timestamp >= NOW() - INTERVAL '48 hours';
                    """)
                    rows = cur.fetchall()
                    for r in rows:
                        fingerprint_hash, raw_text = r
                        if fingerprint_hash:
                            existing_fingerprints.add(fingerprint_hash)
                        elif raw_text:
                            # Fallback for old rows before the migration
                            existing_fingerprints.add(canonical_fingerprint(raw_text))
            logger.info(f"Loaded {len(existing_fingerprints)} existing headline fingerprints from Supabase (last 48h).")
        except Exception as e:
            logger.error(f"Failed to connect to database or fetch recent fingerprints: {e}")
    else:
        logger.warning("DATABASE_URL not set. Skipping actual database insertion.")
    
    # Filter payloads against existing database records to prevent redundant scoring
    fresh_payloads = []
    seen_in_run = set()
    for item in payloads:
        headline = item['data']['headline']
        fp = canonical_fingerprint(headline)
        if not fp:
            continue
        if fp in existing_fingerprints or fp in seen_in_run:
            logger.info(f"Skipping duplicate/already-stored headline: {headline[:60]}...")
            continue
        seen_in_run.add(fp)
        fresh_payloads.append(item)

    logger.info(f"Deduplication summary: {len(payloads)} polled -> {len(fresh_payloads)} fresh payloads to score and store.")
    if not fresh_payloads:
        logger.info("All polled news items are already recorded in Supabase. Zero OPEX wasted.")
        return len(payloads), 0

    # 2 & 3. Score and Insert Fresh Payloads
    for item in fresh_payloads:
        text = f"{item['data']['headline']} - {item['data']['summary']}"
        region = item['region_tag']
        ticker = item.get('index_ticker', 'UNKNOWN')
        asset_class = item.get('asset_class', 'equity')
        
        # Load context
        context = load_okf_rules(region)
        
        # Score via ZeroGPU CLM-8B (or Gemini SDK)
        logger.info(f"Scoring [{region}] {ticker} ({asset_class}) headline: {item['data']['headline'][:50]}...")
        result = score_sentiment(client, text, context, region_tag=region, asset_class=asset_class)
        
        # Guard against LLM formatting hallucinations (e.g., returning a list instead of a dict)
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        if not isinstance(result, dict):
            logger.warning(f"Unexpected AI output format: {type(result)}. Falling back to neutral.")
            result = {}

        # Extract data robustly to prevent KeyError if the LLM hallucinates lowercase JSON keys
        choice_val = str(result.get('Choice', result.get('choice', 'Neutral')))
        
        if "DirectionalScore" in result:
            directional_score = float(result["DirectionalScore"])
            score_val = abs(directional_score)
        else:
            score_val_raw = result.get('Score', result.get('score', 0.5))
            try:
                score_val = float(score_val_raw)
            except (ValueError, TypeError):
                score_val = 0.5
                
            directional_score = score_val
            if choice_val.lower() == 'bearish':
                directional_score = -abs(directional_score)
            elif choice_val.lower() == 'neutral':
                directional_score = 0.0
            
        noul_val = result.get('Noul', result.get('noul', 'No explanation provided.'))
            
        logger.info(f"AI Verdict: {choice_val} | Score: {directional_score:+.4f} | Noul: {noul_val}")
        
        # Calculate fingerprint for insertion
        headline = item['data']['headline']
        fingerprint_hash = canonical_fingerprint(headline)
        
        # Insert into DB (Vertical Partitioning)
        if db_client:
            signal_id = str(uuid.uuid4())
                
            with db_client.get_connection() as conn:
                with conn.cursor() as cur:
                    # Insert Math Layer
                    cur.execute("""
                        INSERT INTO event_signals (id, index_ticker, market_region, timestamp, sentiment_score)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (signal_id, ticker, region, item['data']['timestamp'], directional_score))
                    
                    # Insert Document Layer
                    cur.execute("""
                        INSERT INTO event_payloads (id, timestamp, raw_text, applied_okf_rules, metadata, fingerprint_hash)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (signal_id, item['data']['timestamp'], text, context, json.dumps(item), fingerprint_hash))
                conn.commit()
                
        # Mandatory 4.2-second delay to enforce ~14 requests per minute, respecting Gemini's 15 RPM free tier limit
        # No strict rate limit since we host our own Modal API!
        await asyncio.sleep(0.1)
                
    logger.info("--- Ingestion Pipeline Complete ---\n")
    return len(payloads), len(fresh_payloads)

def run_signal_engine():
    """
    Step 4: Calculate EMA and trigger paper trades via Alpaca.
    (In production, this would be scheduled via Cron, not run immediately after ingestion).
    """
    logger.info("--- Starting Signal Engine (Cron Trigger) ---")
    cron_ema_trigger()
    logger.info("--- Signal Engine Complete ---\n")

if __name__ == "__main__":
    logger.info("Starting Global Sentiment Platform of Share Markets (GSP) Pipeline...")
    
    db_client = None
    if os.environ.get("DATABASE_URL"):
        try:
            db_client = get_db_client()
        except Exception as e:
            logger.warning(f"Could not initialize DB pool for telemetry: {e}")

    # Track pipeline execution telemetry and completion freshness
    with track_pipeline_run("macro_sentiment_pipeline", db_client=db_client) as tracker:
        # 1. Run Async Ingestion & Scoring
        polled_count, scored_count = asyncio.run(run_ingestion_pipeline())
        tracker.record_counts(items_polled=polled_count, items_scored=scored_count)
        
        # 2. Run Signal Engine (Cron)
        run_signal_engine()
    
    logger.info("Pipeline execution finished.")
