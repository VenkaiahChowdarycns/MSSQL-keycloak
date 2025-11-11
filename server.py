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

mcp = FastMCP("MSSQL MCP Server")

# ---- Register as MCP tools (Claude will see these) ----
@mcp.tool()
def mssql_query_tool(query: str, params: Optional[List[Any]] = None):
    return run_query(query, params)

@mcp.tool()
def mssql_insert_tool(table: str, data: Dict[str, Any]):
    return insert_row(table, data)



@mcp.tool()
def mssql_update_tool(table: str, data: Dict[str, Any], condition: Dict[str, Any]):
    return update_row(table, data, condition)

@mcp.tool()
def mssql_delete_tool(table: str, condition: Dict[str, Any]):
    return delete_row(table, condition)

@mcp.tool()
def mssql_schema_tool(table_name: str):
    return get_table_schema(table_name)


if __name__ == "__main__":
    mcp.run()
   