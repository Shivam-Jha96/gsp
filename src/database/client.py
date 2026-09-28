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
    """
    def __init__(self, min_conn: int = 1, max_conn: int = 10):
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is required.")
        
        try:
            self.pool = pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                dsn=self.db_url
            )
            logger.info("Supabase connection pool initialized successfully.")
        except psycopg2.DatabaseError as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for getting a connection from the pool."""
        if not self.pool:
            raise RuntimeError("Connection pool is not initialized.")
            
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

    def close_pool(self):
        """Close all connections in the pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("Supabase connection pool closed.")

# Global instance for the application
_db_client = None

def get_db_client() -> SupabasePoolClient:
    """Returns a singleton instance of the connection pool client."""
    global _db_client
    if _db_client is None:
        _db_client = SupabasePoolClient()
    return _db_client
