# db.py
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv("MSSQL_SERVER", "")
DATABASE = os.getenv("MSSQL_DATABASE", "")
USER = os.getenv("MSSQL_USERNAME", "")
PASSWORD = os.getenv("MSSQL_PASSWORD", "")
DRIVER = os.getenv("MSSQL_DRIVER", "")
TRUSTED = os.getenv("MSSQL_TRUSTED_CONNECTION", "no").lower() in ("1", "true", "yes")

def build_conn_str():
    if TRUSTED:
        return f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;TrustServerCertificate=yes;"
    else:
        return f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};UID={USER};PWD={PASSWORD};TrustServerCertificate=yes;"

def get_connection():
    conn_str = build_conn_str()
    return pyodbc.connect(conn_str)
