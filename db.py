import os
import sys
import logging
import pyodbc
from typing import List, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def log_debug(msg):
    """Logs safely to stderr (so MCP JSON isn't broken)."""
    print(msg, file=sys.stderr, flush=True)

def build_conn_str(db_driver: str, db_server: str, db_port: str, db_user: str, db_password: str, db_name: Optional[str] = None):
    """
    Build ODBC connection string; include DATABASE only if db_name provided.
    """
    server_part = f"{db_server},{db_port}" if db_port else db_server
    parts = [
        f"DRIVER={{{db_driver}}}",
        f"SERVER={server_part}",
    ]
    if db_name:
        parts.append(f"DATABASE={db_name}")
    parts += [
        f"UID={db_user}",
        f"PWD={db_password}",
        "Encrypt=yes",
        "TrustServerCertificate=yes",
        "Connection Timeout=30"
    ]
    return ";".join(parts) + ";"

def get_connection_from_credentials(db_user: str, db_password: str, db_server: str, db_port: str, db_driver: str, db_name: Optional[str] = None, autocommit: bool = False):
    """
    Connect to MSSQL using provided credentials and an explicit db_name when supplied.
    """
    if not all([db_user, db_password, db_server, db_port, db_driver]):
        raise ValueError("Missing DB connection pieces (user/password/server/port/driver).")
    conn_str = build_conn_str(db_driver=db_driver, db_server=db_server, db_port=str(db_port), db_user=db_user, db_password=db_password, db_name=db_name)
    safe_str = conn_str.replace(db_password, "***")
    log_debug(f"[DB] Connecting: {safe_str}")
    try:
        conn = pyodbc.connect(conn_str, autocommit=autocommit)
        logger.info("Connected to %s:%s (db=%s) as %s", db_server, db_port, db_name or "<none>", db_user)
        return conn
    except Exception as e:
        logger.error("Failed to connect to DB %s:%s (db=%s): %s", db_server, db_port, db_name, e)
        raise

def resolve_database_for_table(db_user: str, db_password: str, db_server: str, db_port: str, db_driver: str, table_name: str) -> str:
    """
    Scan all user databases and return the single database that contains table_name.
    If multiple databases contain the table, raise Exception with list of candidates.
    If none found, raise Exception.
    """
    # Connect without database to run queries across DBs
    conn = get_connection_from_credentials(db_user, db_password, db_server, db_port, db_driver, db_name=None, autocommit=True)
    cursor = conn.cursor()
    try:
        # get list of database names (exclude system dbs except master if desired)
        cursor.execute("SELECT name FROM sys.databases WHERE state_desc = 'ONLINE'")
        dbs = [row[0] for row in cursor.fetchall()]
        matches: List[str] = []
        for db in dbs:
            try:
                # Query INFORMATION_SCHEMA.TABLES in target database using three-part name
                sql = f"SELECT 1 FROM [{db}].INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?"
                c2 = conn.cursor()
                c2.execute(sql, (table_name,))
                row = c2.fetchone()
                c2.close()
                if row:
                    matches.append(db)
            except Exception:
                # ignore DBs we can't access
                continue
        if not matches:
            raise Exception(f"Database not found for table '{table_name}'")
        if len(matches) > 1:
            raise Exception(f"Table '{table_name}' exists in multiple databases: {matches}")
        return matches[0]
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def list_all_databases(db_user: str, db_password: str, db_server: str, db_port: str, db_driver: str) -> List[str]:
    """
    Return a list of all ONLINE user-accessible SQL Server databases.
    Exclude system DBs: master, tempdb, model, msdb.
    """
    conn = get_connection_from_credentials(
        db_user=db_user,
        db_password=db_password,
        db_server=db_server,
        db_port=db_port,
        db_driver=db_driver,
        db_name=None,
        autocommit=True,
    )
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sys.databases WHERE state_desc = 'ONLINE'")
        names = [row[0] for row in cursor.fetchall()]
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

    # exclude system DBs
    return [n for n in names if n.lower() not in ('master', 'tempdb', 'model', 'msdb')]
