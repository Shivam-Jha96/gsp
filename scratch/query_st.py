import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from database.client import get_db_client

db_client = get_db_client()
with db_client.get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT s.sentiment_score, p.raw_text FROM event_signals s JOIN event_payloads p ON s.id=p.id WHERE p.raw_text ILIKE '%Nasdaq Hits High%'")
        print('Hits High:', cur.fetchall())
        cur.execute("SELECT s.sentiment_score, p.raw_text FROM event_signals s JOIN event_payloads p ON s.id=p.id WHERE p.raw_text ILIKE '%closes just below a record%'")
        print('Closes just below:', cur.fetchall())
