import psycopg2
import os

url = os.environ.get('DATABASE_URL')
if not url:
    print('NO DATABASE URL')
else:
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("SELECT s.sentiment_score, p.raw_text FROM event_signals s JOIN event_payloads p ON s.id=p.id WHERE p.raw_text ILIKE '%Nasdaq Hits High%'")
        print('Hits High:', cur.fetchall())
        cur.execute("SELECT s.sentiment_score, p.raw_text FROM event_signals s JOIN event_payloads p ON s.id=p.id WHERE p.raw_text ILIKE '%closes just below a record%'")
        print('Closes just below:', cur.fetchall())
    except Exception as e:
        print('ERROR:', e)
