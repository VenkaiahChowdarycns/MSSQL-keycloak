# db.py
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

SERVER   = os.getenv("MSSQL_SERVER", "host.docker.internal")
PORT     = os.getenv("MSSQL_PORT", "1433")
DATABASE = os.getenv("MSSQL_DATABASE", "master")
USER     = os.getenv("MSSQL_USER", "sa")
PASSWORD = os.getenv("MSSQL_PASSWORD", "")
DRIVER   = os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server")
ENCRYPT  = os.getenv("MSSQL_ENCRYPT", "yes")

def build_conn_str():
    return (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER},{PORT};"
        f"DATABASE={DATABASE};"
        f"UID={USER};PWD={PASSWORD};"
        f"Encrypt={ENCRYPT};"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=30;"
    )

def get_connection(autocommit=True):
    conn_str = build_conn_str()
    print(f"[DB] Connecting: {conn_str.replace(PASSWORD, '***')}", flush=True)
    conn = pyodbc.connect(conn_str, autocommit=autocommit)
    return conn