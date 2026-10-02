import asyncio
import logging
import os
import json
import uuid

# Ingestion
from ingestion.poller import FeedPoller, FEEDS

# AI Engine (TypeSafe AI - Jev System-One Model)
from typesafe_sdk import TypeSafeClient, Choice

def score_sentiment(client, text: str, region_context: str) -> dict:
    """
    Sends the text and context to TypeSafe AI's Jev model using the official SDK.
    Computes Net Directional Probability Vector: P(Bullish) - P(Bearish) calibrated
    against the relative directional conviction to produce an accurate [-1.0, 1.0] score.
    """
    try:
        # We define a structured State using our text and OKF Rules
        state_content = f"""Regional Context (OKF Rules):
{region_context}

Text to analyze: {text}"""

        # Jev evaluates states purely via predefined Choices
        result = client.system_one(
            state=state_content,
            questions={
                "direction": Choice(
                    instructions="Determine the market direction implied by the text according to the OKF Rules.",
                    criteria={"Bullish": None, "Bearish": None, "Neutral": None}
                )
            }
        )
        
        # Extract the structured decisions natively
        choice_obj = result.choices["direction"]
        choice_str = choice_obj.choice.capitalize()
        probs = choice_obj.probabilities or {}
        
        p_bull = float(probs.get("Bullish", 0.0))
        p_bear = float(probs.get("Bearish", 0.0))
        p_neut = float(probs.get("Neutral", 0.0))
        
        # Relative directional spread: (P_bull - P_bear) / (P_bull + P_bear)
        dir_sum = p_bull + p_bear
        if dir_sum > 1e-5:
            s_rel = (p_bull - p_bear) / dir_sum
        else:
            s_rel = 0.0
            
        # Directional sentiment: if model decides Neutral, center at 0.0
        if choice_str.lower() == "neutral":
            directional_score = 0.0
            score_magnitude = 0.0
        elif choice_str.lower() == "bearish":
            # Scale by certainty (1 - 0.5 * P_neutral)
            magnitude = abs(s_rel) * (1.0 - 0.5 * p_neut)
            directional_score = -abs(magnitude)
            score_magnitude = abs(directional_score)
        else: # Bullish
            magnitude = abs(s_rel) * (1.0 - 0.5 * p_neut)
            directional_score = abs(magnitude)
            score_magnitude = abs(directional_score)
            
        # Clamp to [-1.0, 1.0]
        directional_score = max(-1.0, min(1.0, directional_score))
        score_magnitude = max(0.0, min(1.0, score_magnitude))
        
        return {
            "Choice": choice_str,
            "Score": score_magnitude,
            "DirectionalScore": directional_score,
            "Probabilities": probs,
            "Noul": f"Evaluated via TypeSafe Jev (P_bull={p_bull:.2f}, P_bear={p_bear:.2f}, P_neut={p_neut:.2f})"
        }
        
    except Exception as e:
        logging.error(f"Failed to reach TypeSafe API: {e}")
        return {"Choice": "Neutral", "Score": 0.0, "DirectionalScore": 0.0, "Noul": f"API Error: {e}"}

# Database
from database.client import get_db_client

# Signal Engine
from signal_engine.cron_jobs import cron_ema_trigger

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def load_okf_rules(region_tag: str) -> str:
    """Loads the regional OKF markdown rules based on the region tag."""
    # Mapping region tags to their respective OKF files
    file_map = {
        "US": "us_macro.okf.md",
        "IN": "india_macro.okf.md",
        "UK": "uk_macro.okf.md",
        "JP": "japan_macro.okf.md",
    }
    
    filename = file_map.get(region_tag)
    if not filename:
        return "No specific macro rules for this region."
        
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Knowledge file {filename} not found.")
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
        return

    # Connect to the custom serverless Modal deployment running Contrastive-LM
    typesafe_api_key = os.environ.get('TYPESAFE_API_KEY')
    client = TypeSafeClient(api_key=typesafe_api_key.strip() if typesafe_api_key else 'empty_key_allowed', base_url='https://shivam-jha96--clm-macro-engine-clm-server.modal.run', model='clm-latest', timeout=120.0)

    # Initialize DB (Requires DATABASE_URL environment variable)
    db_client = None
    if os.environ.get("DATABASE_URL"):
        try:
            db_client = get_db_client()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
    else:
        logger.warning("DATABASE_URL not set. Skipping actual database insertion.")
    
    # 2 & 3. Score and Insert
    for item in payloads:
        text = f"{item['data']['headline']} - {item['data']['summary']}"
        region = item['region_tag']
        ticker = item.get('index_ticker', 'UNKNOWN')
        
        # Load context
        context = load_okf_rules(region)
        
        # Score via ZeroGPU CLM-8B (or Gemini SDK)
        logger.info(f"Scoring [{region}] {ticker} headline: {item['data']['headline'][:50]}...")
        result = score_sentiment(client, text, context)
        
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
                        INSERT INTO event_payloads (id, raw_text, applied_okf_rules, metadata)
                        VALUES (%s, %s, %s, %s)
                    """, (signal_id, text, context, json.dumps(item)))
                conn.commit()
                
        # Mandatory 4.2-second delay to enforce ~14 requests per minute, respecting Gemini's 15 RPM free tier limit
        # No strict rate limit since we host our own Modal API!
        await asyncio.sleep(0.1)
                
    logger.info("--- Ingestion Pipeline Complete ---\n")

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
    
    # 1. Run Async Ingestion & Scoring
    asyncio.run(run_ingestion_pipeline())
    
    # 2. Run Signal Engine (Cron)
    run_signal_engine()
    
    logger.info("Pipeline execution finished.")
