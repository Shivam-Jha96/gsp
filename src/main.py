import asyncio
import logging
import os
import json
import uuid

# Ingestion
from ingestion.poller import FeedPoller, FEEDS

# AI Engine (Google Gemini Pro SDK)
import google.generativeai as genai

def score_sentiment(text: str, region_context: str) -> dict:
    """
    Sends the text and context to the Gemini Pro model using the robust official SDK.
    Expects GEMINI_API_KEY environment variable.
    """
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not gemini_api_key:
        logging.warning("GEMINI_API_KEY not set. AI scoring will be mocked.")
        return {"Choice": "Neutral", "Score": 0.5, "Noul": "Mocked response due to missing GEMINI_API_KEY."}
        
    try:
        genai.configure(api_key=gemini_api_key.strip())
        
        # You mentioned having a Gemini Pro account, so we'll target the Pro model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={"response_mime_type": "application/json", "temperature": 0.1}
        )
        
        prompt = f"""You are an AI financial analyst. Analyze the text based on the provided regional macro rules.
Regional Context (OKF Rules):
{region_context}

Text to analyze: {text}

Output EXACTLY and ONLY a JSON object in this format, with no extra text:
{{"Choice": "Bullish", "Score": 0.85, "Noul": "Explanation here"}}
(Choice must be Bullish, Bearish, or Neutral. Score must be between 0.0 and 1.0)"""

        response = model.generate_content(prompt)
        
        # The SDK cleanly extracts the text response
        return json.loads(response.text)
        
    except Exception as e:
        logging.error(f"Failed to reach Gemini SDK API: {e}")
        return {"Choice": "Neutral", "Score": 0.5, "Noul": f"API Error: {e}"}

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
        # Add others as they are created
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
        
        # Load context
        context = load_okf_rules(region)
        
        # Score via ZeroGPU CLM-8B
        logger.info(f"Scoring [{region}] headline: {item['data']['headline'][:50]}...")
        result = score_sentiment(text, context)
        logger.info(f"AI Verdict: {result['Choice']} | Score: {result['Score']} | Noul: {result['Noul']}")
        
        # Insert into DB (Vertical Partitioning)
        if db_client:
            signal_id = str(uuid.uuid4())
            with db_client.get_connection() as conn:
                with conn.cursor() as cur:
                    # Insert Math Layer
                    cur.execute("""
                        INSERT INTO event_signals (id, index_ticker, market_region, timestamp, sentiment_score)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (signal_id, "UNKNOWN", region, item['data']['timestamp'], result['Score']))
                    
                    # Insert Document Layer
                    cur.execute("""
                        INSERT INTO event_payloads (id, raw_text, applied_okf_rules, metadata)
                        VALUES (%s, %s, %s, %s)
                    """, (signal_id, text, context, json.dumps(item)))
                conn.commit()
                
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
    logger.info("Starting Global Macro-Sentiment Tracker Pipeline...")
    
    # 1. Run Async Ingestion & Scoring
    asyncio.run(run_ingestion_pipeline())
    
    # 2. Run Signal Engine (Cron)
    run_signal_engine()
    
    logger.info("Pipeline execution finished.")
