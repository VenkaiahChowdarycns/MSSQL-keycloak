import json
import logging
import time
from getpass import getpass

from mcp.server.fastmcp import FastMCP

from keycloak_integration import (
    get_token,
    refresh_access_token,
    verify_token,
    get_user_db_attrs,
)
from db import list_all_databases, get_connection_from_credentials

# SHARED GLOBAL STATE
import state

# Tools
from tools.mssql_query import run_query
from tools.mssql_insert import insert_row
from tools.mssql_update import update_row
from tools.mssql_delete import delete_row
from tools.mssql_schema import get_table_schema


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MSSQL-MCP")

mcp = FastMCP("MSSQL MCP Server")


# ---------------------------------------------------
def get_conn(db_name: str):
    if db_name not in state.DB_CREDS:
        raise Exception(f"Invalid database name '{db_name}'. Available: {list(state.DB_CREDS.keys())}")
    creds = state.DB_CREDS[db_name]
    return get_connection_from_credentials(
        db_user=creds["db_user"],
        db_password=creds["db_password"],
        db_server=creds["db_server"],
        db_port=creds["db_port"],
        db_driver=creds["db_driver"],
        db_name=creds.get("db_database"),
    )


def ensure_fresh_token():
    """
    Ensure the access token is valid, refreshing it if needed.
    Returns None on success, or an error dict if re-login is required.
    """
    now = int(time.time())

    # Refresh token expired: force login
    if now >= state.REFRESH_TOKEN_EXPIRES_AT:
        return {"error": "Token expired, please login again"}

    # Access token expired: try to refresh
    if now >= state.ACCESS_TOKEN_EXPIRES_AT:
        try:
            tokens = refresh_access_token(state.REFRESH_TOKEN)
        except Exception:
            return {"error": "Token expired, please login again"}

        state.ACCESS_TOKEN = tokens["access_token"]
        state.REFRESH_TOKEN = tokens["refresh_token"]
        state.ACCESS_TOKEN_EXPIRES_AT = now + int(tokens.get("expires_in", 300))
        state.REFRESH_TOKEN_EXPIRES_AT = now + int(tokens.get("refresh_expires_in", 1800))

    return None


def require_auth():
    if not state.logged_in_user or not state.ACCESS_TOKEN:
        return {"status": "error", "message": "Login required"}
    try:
        verify_token(state.ACCESS_TOKEN)
        return None
    except Exception:
        return {"status": "error", "message": "Invalid or expired token"}


def _normalize_params(params):
    if isinstance(params, str):
        try:
            parsed = json.loads(params)
            return parsed if isinstance(parsed, list) else [parsed]
        except Exception:
            return [params]
    if params is None:
        return []
    return params if isinstance(params, list) else [params]


# -------------------- TOOLS ------------------------
@mcp.tool()
def mssql_query_tool(query: str, params=None, db_name="default"):
    freshness = ensure_fresh_token()
    if freshness:
        return freshness

    auth = require_auth()
    if auth:
        return auth

    try:
        return run_query(query, _normalize_params(params), db_name=db_name)
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@mcp.tool()
def mssql_insert_tool(table: str, data, db_name="default"):
    freshness = ensure_fresh_token()
    if freshness:
        return freshness

    auth = require_auth()
    if auth:
        return auth

    try:
        return insert_row(table, data, db_name=db_name)
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@mcp.tool()
def mssql_update_tool(table: str, data, condition, db_name="default"):
    freshness = ensure_fresh_token()
    if freshness:
        return freshness

    auth = require_auth()
    if auth:
        return auth

    try:
        return update_row(table, data, condition, db_name=db_name)
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@mcp.tool()
def mssql_delete_tool(table: str, condition, db_name="default"):
    freshness = ensure_fresh_token()
    if freshness:
        return freshness

    auth = require_auth()
    if auth:
        return auth

    try:
        return delete_row(table, condition, db_name=db_name)
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@mcp.tool()
def mssql_schema_tool(table_name: str, db_name="default"):
    freshness = ensure_fresh_token()
    if freshness:
        return freshness

    auth = require_auth()
    if auth:
        return auth

    try:
        return get_table_schema(table_name, db_name=db_name)
    except Exception as e:
        return {"status": "error", "reason": str(e)}


# -------------------- LOGIN ------------------------
def cli_login():
    print("🔐 Keycloak Login")

    while True:
        username = input("Username: ").strip()
        password = getpass("Password: ")

        try:
            tokens = get_token(username, password)
            now = int(time.time())

            state.ACCESS_TOKEN = tokens["access_token"]
            state.REFRESH_TOKEN = tokens["refresh_token"]
            state.ACCESS_TOKEN_EXPIRES_AT = now + int(tokens.get("expires_in", 300))
            state.REFRESH_TOKEN_EXPIRES_AT = now + int(tokens.get("refresh_expires_in", 1800))
            state.logged_in_user = username

            print("\n🔑 Access Token:")
            print(state.ACCESS_TOKEN)

            # Fetch DB attrs from Keycloak
            raw = get_user_db_attrs(username)

            creds = {
                "db_user": raw["db_user"],
                "db_password": raw["db_password"],
                "db_server": raw["db_server"],
                "db_port": raw["db_port"],
                "db_driver": raw["db_driver"],
            }

            # Discover DBs
            dbs = list_all_databases(
                creds["db_user"],
                creds["db_password"],
                creds["db_server"],
                creds["db_port"],
                creds["db_driver"],
            )

            state.DB_CREDS = {}

            # default if provided
            preferred = raw.get("db_database")

            if preferred:
                state.DB_CREDS[preferred] = {**creds, "db_database": preferred}

            for d in dbs:
                state.DB_CREDS[d] = {**creds, "db_database": d}

            # Set default
            if preferred:
                state.DB_CREDS["default"] = state.DB_CREDS[preferred]
            else:
                state.DB_CREDS["default"] = state.DB_CREDS[dbs[0]]

            print(f"\n🗄 Databases available ({len(dbs)}):")
            for d in dbs:
                print(" •", d)
            print("Default =", "default")

            break

        except Exception as e:
            print("❌ Login failed:", e)


# -------------------- MAIN ------------------------
if __name__ == "__main__":
    cli_login()
    logger.info("🚀 Starting MSSQL MCP Server")
    mcp.run(transport="streamable-http")