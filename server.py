# server.py
# ========================================
# 1. IMPORTS
# ========================================
import logging
import sys
from typing import Optional, List, Any, Dict
from dotenv import load_dotenv

load_dotenv()

from fastmcp import FastMCP
from keycloak_integration import get_user_info_from_token, extract_db_credentials, get_connection_from_token
from tools.mssql_query import run_query
from tools.mssql_insert import insert_row
from tools.mssql_update import update_row
from tools.mssql_delete import delete_row
from tools.mssql_schema import get_table_schema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# 2. INIT MCP
# ========================================
mcp = FastMCP("MSSQL MCP Server")

# ========================================
# 3. AUTH HELPERS
# ========================================
def get_access_token(authorization: Optional[str]) -> str:
    """
    Extract and validate Bearer token from Authorization header.
    Raises ValueError on missing or invalid format.
    """
    if not authorization:
        raise ValueError("Missing Authorization header")
    
    if not authorization.startswith("Bearer "):
        raise ValueError("Invalid token format. Expected 'Bearer <token>'")
    
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise ValueError("Empty token")
    
    return token

def validate_and_get_user(authorization: Optional[str]) -> dict:
    """
    Validate Bearer token and return Keycloak user info.
    Raises ValueError on auth failure.
    """
    try:
        access_token = get_access_token(authorization)
    except ValueError as e:
        raise ValueError(f"Auth error: {e}")
    
    user_info = get_user_info_from_token(access_token)
    if not user_info:
        raise ValueError("Invalid or expired token")
    
    return user_info

# ========================================
# 4. REGISTER TOOLS
# ========================================
@mcp.tool()
def mssql_query_tool(
    query: str,
    params: Optional[List[Any]] = None,
    authorization: Optional[str] = None,
):
    """Execute a SELECT query against MSSQL using user's Keycloak credentials."""
    try:
        user_info = validate_and_get_user(authorization)
        db_user, _ = extract_db_credentials(user_info)
        logger.info(f"Query executed by Keycloak user: {user_info.get('preferred_username')}")
    except ValueError as e:
        return {"success": False, "error": str(e), "status_code": 401}
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 403}
    
    try:
        conn = get_connection_from_token(authorization)
        result = run_query(query, params, conn=conn)
        return result
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def mssql_insert_tool(
    table: str,
    data: Dict[str, Any],
    authorization: Optional[str] = None,
):
    """Insert a row into an MSSQL table using user's Keycloak credentials."""
    try:
        user_info = validate_and_get_user(authorization)
        extract_db_credentials(user_info)
        logger.info(f"Insert to {table} by Keycloak user: {user_info.get('preferred_username')}")
    except ValueError as e:
        return {"success": False, "error": str(e), "status_code": 401}
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 403}
    
    try:
        conn = get_connection_from_token(authorization)
        result = insert_row(table, data, conn=conn)
        return result
    except Exception as e:
        logger.error(f"Insert failed: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def mssql_update_tool(
    table: str,
    data: Dict[str, Any],
    condition: Dict[str, Any],
    authorization: Optional[str] = None,
):
    """Update row(s) in an MSSQL table using user's Keycloak credentials."""
    try:
        user_info = validate_and_get_user(authorization)
        extract_db_credentials(user_info)
        logger.info(f"Update {table} by Keycloak user: {user_info.get('preferred_username')}")
    except ValueError as e:
        return {"success": False, "error": str(e), "status_code": 401}
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 403}
    
    try:
        conn = get_connection_from_token(authorization)
        result = update_row(table, data, condition, conn=conn)
        return result
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def mssql_delete_tool(
    table: str,
    condition: Dict[str, Any],
    authorization: Optional[str] = None,
):
    """Delete row(s) from an MSSQL table using user's Keycloak credentials."""
    try:
        user_info = validate_and_get_user(authorization)
        extract_db_credentials(user_info)
        logger.info(f"Delete from {table} by Keycloak user: {user_info.get('preferred_username')}")
    except ValueError as e:
        return {"success": False, "error": str(e), "status_code": 401}
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 403}
    
    try:
        conn = get_connection_from_token(authorization)
        result = delete_row(table, condition, conn=conn)
        return result
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def mssql_schema_tool(
    table_name: str,
    authorization: Optional[str] = None,
):
    """Get schema information for an MSSQL table using user's Keycloak credentials."""
    try:
        user_info = validate_and_get_user(authorization)
        extract_db_credentials(user_info)
        logger.info(f"Schema query by Keycloak user: {user_info.get('preferred_username')}")
    except ValueError as e:
        return {"success": False, "error": str(e), "status_code": 401}
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 403}
    
    try:
        conn = get_connection_from_token(authorization)
        result = get_table_schema(table_name, conn=conn)
        return result
    except Exception as e:
        logger.error(f"Schema query failed: {e}")
        return {"success": False, "error": str(e)}

# ========================================
# 5. START SERVER
# ========================================
if __name__ == "__main__":
    # Pre-flight checks
    logger.info("=" * 80)
    logger.info("🚀 MSSQL MCP Server - Pre-flight Checks")
    logger.info("=" * 80)
    
    # Check Keycloak connectivity
    try:
        from keycloak_health_check import check_keycloak_connectivity
        success, message = check_keycloak_connectivity()
        if not success:
            logger.error(f"❌ Keycloak check failed: {message}")
            logger.error("⚠️  Server startup aborted due to Keycloak connection failure")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("✅ All pre-flight checks passed")
    logger.info("=" * 80)
    logger.info("📋 Registered Tools:")
    for tool in mcp._tools:
        logger.info(f"   ✓ {tool.name}")
    logger.info("🔐 Authentication: Keycloak OpenID Connect (JWT)")
    logger.info("📊 Authorization: Per-user MSSQL credentials from Keycloak attributes")
    logger.info("=" * 80)
    logger.info("Starting MCP server on streamable-http transport...\n")
    
    mcp.run(transport="streamable-http")
