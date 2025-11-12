import os
import sys
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def log_debug(msg):
    """Logs safely to stderr (so MCP JSON isn't broken)."""
    print(msg, file=sys.stderr, flush=True)

def get_db_config(db_key: str = "DB1"):
    """Fetch connection settings for the given database key (e.g., DB1, DB2, DB3)."""
    prefix = f"MSSQL_{db_key.upper()}_"
    return {
        "server": os.getenv("MSSQL_SERVER", "host.docker.internal"),
        "port": os.getenv("MSSQL_PORT", "1433"),
        "database": os.getenv(prefix + "NAME", "master"),
        "user": os.getenv(prefix + "USER", "sa"),
        "password": os.getenv(prefix + "PASSWORD", ""),
        "driver": os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server"),
        "encrypt": os.getenv("MSSQL_ENCRYPT", "yes"),
        "trusted": os.getenv("MSSQL_TRUSTED_CONNECTION", "no").lower() in ("1", "true", "yes"),
    }

def build_conn_str(config: dict):
    return (
        f"DRIVER={{{config['driver']}}};"
        f"SERVER={config['server']},{config['port']};"
        f"DATABASE={config['database']};"
        f"UID={config['user']};PWD={config['password']};"
        f"Encrypt={config['encrypt']};"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=30;"
    )

def get_connection(db_key: str = "DB1", autocommit=True):
    """Establish connection to a specific MSSQL database (DB1, DB2, DB3...)."""
    config = get_db_config(db_key)
    conn_str = build_conn_str(config)
    safe_str = conn_str.replace(config["password"], "***")
    log_debug(f"[DB] Connecting ({db_key}): {safe_str}")
    conn = pyodbc.connect(conn_str, autocommit=autocommit)
    return conn
