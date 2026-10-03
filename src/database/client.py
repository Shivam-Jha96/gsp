import os
import logging
from contextlib import contextmanager
from psycopg2 import pool
import psycopg2

logger = logging.getLogger(__name__)

class SupabasePoolClient:
    """
    Handles Supabase PostgreSQL connection pooling logic.
    Assumes DATABASE_URL points to the Supabase connection pooler
    (typically port 6543 for transaction mode pooling).
    Includes proactive TCP keepalive probes, pre-checkout liveness validation,
    and automatic dead-connection recycling to prevent idle disconnect errors.
    """
    def __init__(self, min_conn: int = 1, max_conn: int = 10):
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is required.")
        
        self.min_conn = min_conn
        self.max_conn = max_conn
        self.pool = None
        self._init_pool()

    def _init_pool(self):
        """Initializes the ThreadedConnectionPool with TCP keepalive configurations."""
        try:
            self.pool = pool.ThreadedConnectionPool(
                minconn=self.min_conn,
                maxconn=self.max_conn,
                dsn=self.db_url,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            logger.info("Supabase connection pool initialized successfully with TCP keepalives.")
        except psycopg2.DatabaseError as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def _is_alive(self, conn) -> bool:
        """Lightweight check to verify connection is alive and healthy."""
        if conn is None or conn.closed != 0:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
            return True
        except Exception:
            return False

    def _get_valid_connection(self):
        """
        Retrieves an active, verified connection from the pool.
        Dead connections (e.g., terminated by remote Supabase pooler during idle periods)
        are cleanly closed and discarded from the pool rather than returned to callers.
        """
        if self.pool is None or self.pool.closed:
            self._init_pool()

        # Retry up to max_conn times to find or establish a live connection
        for attempt in range(max(self.max_conn, 3)):
            conn = self.pool.getconn()
            if self._is_alive(conn):
                return conn
            
            # Connection is dead; discard it from the pool using close=True
            logger.warning(f"Discarding stale connection (attempt {attempt + 1})")
            try:
                self.pool.putconn(conn, close=True)
            except Exception as e:
                logger.debug(f"Error closing dead connection: {e}")
        
        # If all existing connections in the pool were stale, re-initialize pool
        logger.warning("Re-initializing connection pool after exhaustive stale connection cleanup.")
        self.close_pool()
        self._init_pool()
        return self.pool.getconn()

    @contextmanager
    def get_connection(self):
        """
        Context manager for getting a verified connection from the pool.
        Ensures broken connections during execution are discarded with close=True
        rather than returned to pollute the pool.
        """
        conn = self._get_valid_connection()
        is_broken = False
        try:
            yield conn
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as conn_err:
            is_broken = True
            logger.warning(f"Connection dropped during query execution: {conn_err}")
            raise
        except Exception:
            if conn.closed != 0:
                is_broken = True
            raise
        finally:
            try:
                self.pool.putconn(conn, close=is_broken)
            except Exception as put_err:
                logger.warning(f"Error returning connection to pool: {put_err}")

    def close_pool(self):
        """Close all connections in the pool."""
        if self.pool:
            try:
                self.pool.closeall()
            except Exception as e:
                logger.warning(f"Error closing connection pool: {e}")
            self.pool = None
            logger.info("Supabase connection pool closed.")

# Global instance for the application
_db_client = None

def get_db_client() -> SupabasePoolClient:
    """Returns a singleton instance of the connection pool client."""
    global _db_client
    if _db_client is None:
        _db_client = SupabasePoolClient()
    return _db_client

def reset_db_client():
    """Resets and recreates the global database pool client."""
    global _db_client
    if _db_client is not None:
        try:
            _db_client.close_pool()
        except Exception as e:
            logger.warning(f"Error resetting DB client pool: {e}")
        _db_client = None
    logger.info("Global DB client reset complete.")
