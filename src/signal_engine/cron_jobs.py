import os
import logging
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Import the EMA calculator
from .ema import calculate_ema

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Execution Configuration: Disabled by default for MVP (Signal-Only Engine)
ENABLE_TRADE_EXECUTION = os.getenv("ENABLE_TRADE_EXECUTION", "false").lower() == "true"
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "dummy_api_key")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "dummy_secret_key")
PAPER_TRADING = True

def get_mock_sentiment_data() -> pd.DataFrame:
    """
    Generates mock sentiment data for the MVP.
    In production, this would query a database or API for real sentiment scores.
    """
    # Create 10 hours of mock data ending now
    now = pd.Timestamp.now('UTC')
    dates = pd.date_range(end=now, periods=10, freq='h')
    
    # Simple mock data: alternating sentiment or any pattern
    import numpy as np
    # Random uniform scores between -1 (extreme negative) and 1 (extreme positive)
    np.random.seed(42) # For reproducibility in MVP
    scores = np.random.uniform(-1, 1, size=len(dates))
    
    return pd.DataFrame({"sentiment_score": scores}, index=dates)

def execute_signal(current_ema: float, previous_ema: float, symbol: str = "SPY", qty: float = 1.0):
    """
    Evaluates directional signals based on EMA crossovers.
    In MVP mode, logs directional stance without active order execution.
    """
    # Directional Stance:
    # If EMA goes from negative/lower to positive/higher -> BUY
    # If EMA goes from positive/higher to negative/lower -> SELL
    side = None
    if current_ema > previous_ema and current_ema > 0:
        side = OrderSide.BUY
        stance = "BULLISH"
    elif current_ema < previous_ema and current_ema < 0:
        side = OrderSide.SELL
        stance = "BEARISH"
    else:
        stance = "NEUTRAL"

    if stance == "NEUTRAL":
        logger.info(f"[SIGNAL ENGINE] {symbol} Neutral Deadband -> EMA: {current_ema:+.4f} (Prev: {previous_ema:+.4f}). No action.")
        return

    logger.info(f"[SIGNAL ENGINE] {symbol} {stance} Stance Detected -> EMA: {current_ema:+.4f} (Prev: {previous_ema:+.4f})")

    if not ENABLE_TRADE_EXECUTION:
        logger.info(f"[MVP MODE] Trade execution is disabled. Directional signal recorded for research evaluation.")
        return

    try:
        trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=PAPER_TRADING)
        if side:
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.GTC
            )
            logger.info(f"Routing {side.name} order for {qty} {symbol} to Alpaca Paper Trading...")
            order = trading_client.submit_order(order_data=order_data)
            logger.info(f"Order successful! Order ID: {order.id}")
            
    except Exception as e:
        logger.error(f"Error executing trade signal: {e}")

def cron_ema_trigger():
    """
    The main cron job handler to fetch sentiment, calculate EMA, and execute trades.
    """
    logger.info("Cron Job Started: Evaluating Macro-Sentiment EMA Strategy")
    
    # 1. Fetch the latest sentiment data
    sentiment_df = get_mock_sentiment_data()
    
    # 2. Calculate the 4-hour EMA
    # Assuming the data frequency is hourly, span=4 translates to a 4-period (4-hour) EMA
    ema_series = calculate_ema(sentiment_df, window=4)
    
    if len(ema_series) < 2:
        logger.warning("Insufficient data to calculate EMA crossover. Exiting.")
        return
        
    # 3. Extract the latest and previous EMA values for crossover logic
    current_ema = ema_series.iloc[-1]
    previous_ema = ema_series.iloc[-2]
    
    logger.info(f"4-Hour EMA calculated. Current: {current_ema:.4f} | Previous: {previous_ema:.4f}")
    
    # 4. Route signals to execution layer
    execute_signal(current_ema, previous_ema)
    
    logger.info("Cron Job Completed.")

if __name__ == "__main__":
    # Execute the cron job when run directly
    cron_ema_trigger()
