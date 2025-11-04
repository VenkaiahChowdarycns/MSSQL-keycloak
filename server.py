# server.py
from fastmcp import FastMCP
from typing import Optional, List, Any, Dict

# load .env via db import side effects if needed
from dotenv import load_dotenv
load_dotenv()

# tools
from tools.mssql_query import run_query
from tools.mssql_insert import insert_row
from tools.mssql_update import update_row
from tools.mssql_delete import delete_row
from tools.mssql_schema import get_table_schema
from tools.mssql_health import check_health
import json

mcp = FastMCP("MSSQL MCP Server")


@mcp.tool()
def mssql_query_tool(query: str, params: Any = None):
    """Execute SQL query with optional params"""
    # Normalize params if it's a string or None
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            
            params = [params]
    elif params is None:
        params = []
    elif not isinstance(params, list):
        params = [params]
    return run_query(query, params)

@mcp.tool()
def mssql_insert_tool(table: str, data):
    print(f"🟩 Raw data received from MCP: {repr(data)}")
    return insert_row(table, data)

@mcp.tool()
def mssql_update_tool(table: str, data, condition):
    return update_row(table, data, condition)

@mcp.tool()
def mssql_delete_tool(table: str, condition):
    return delete_row(table, condition)

@mcp.tool()
def mssql_schema_tool(table_name: str):
    return get_table_schema(table_name)

@mcp.tool()
def mssql_health_tool():
    return check_health()

if __name__ == "__main__":
    print("Realtime MSSQL MCP Server running at http://127.0.0.1:8080")
    # Run the MCP server directly
    mcp.run(transport="http", host="127.0.0.1", port=8080)
