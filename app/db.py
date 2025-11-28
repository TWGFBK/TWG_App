import os
import psycopg
from psycopg_pool import ConnectionPool
from contextlib import contextmanager

# Global connection pool
pool = None

def init_db():
    global pool
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/alarm')
    pool = ConnectionPool(database_url, min_size=1, max_size=10)

def close_db():
    global pool
    if pool:
        pool.close()

@contextmanager
def get_connection():
    if not pool:
        init_db()
    with pool.connection() as conn:
        yield conn

def sql_one(query, *params):
    """Execute query and return single row or None"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

def sql_all(query, *params):
    """Execute query and return all rows"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

def sql_exec(query, *params):
    """Execute query without returning results"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()

def run_migrations():
    """Run all migration files in order"""
    migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations')
    
    # Get list of migration files
    migration_files = []
    for filename in os.listdir(migrations_dir):
        if filename.endswith('.sql') and filename[0].isdigit():
            migration_files.append(filename)
    
    migration_files.sort()
    
    # Check which migrations have been applied
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Create migrations table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            
            # Get applied migrations
            cur.execute("SELECT version FROM schema_migrations ORDER BY version")
            applied = {row[0] for row in cur.fetchall()}
    
    # Apply new migrations
    for filename in migration_files:
        if filename not in applied:
            print(f"Applying migration: {filename}")
            migration_path = os.path.join(migrations_dir, filename)
            
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (filename,))
                    conn.commit()
            
            print(f"Applied migration: {filename}")
