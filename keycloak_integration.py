import os
from keycloak import KeycloakOpenID
from db import get_connection as get_db_connection_direct
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keycloak server configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://host.docker.internal:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "mssql-mcp")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "mssql-mcp-server")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")

keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM,
    client_secret_key=KEYCLOAK_CLIENT_SECRET,
)

def _normalize_token(token: str) -> str:
    """Strip common prefixes like 'Bearer ' and whitespace."""
    if not token or not isinstance(token, str):
        return token
    return token.strip().removeprefix("Bearer ").strip()

def _extract_attr(user_info: dict, key: str):
    """
    Extract attribute supporting both top-level keys and Keycloak 'attributes' map,
    where values are often lists.
    """
    # direct key
    val = user_info.get(key)
    if val:
        if isinstance(val, list) and val:
            return val[0]
        return val

    # nested attributes
    attrs = user_info.get("attributes") or {}
    attr_val = attrs.get(key)
    if isinstance(attr_val, list) and attr_val:
        return attr_val[0]
    return attr_val

def get_user_info_from_token(access_token: str):
    """
    Decode the access token to get user information from Keycloak.
    Returns a dict on success, None on failure.
    """
    token = _normalize_token(access_token)
    if not token:
        logger.error("No access token provided.")
        return None

    try:
        user_info = keycloak_openid.userinfo(token)
        logger.debug("Retrieved userinfo for user: %s", user_info.get("preferred_username", "unknown"))
        return user_info
    except Exception as e:
        logger.error("Failed to decode token or get user info: %s", e)
        return None

def extract_db_credentials(user_info: dict) -> tuple:
    """
    Extract MSSQL credentials from Keycloak user attributes.
    Returns: (db_user, db_password)
    Raises: Exception if credentials not found
    """
    if not user_info:
        raise Exception("No user info provided.")

    db_user = _extract_attr(user_info, "db_user")
    db_password = _extract_attr(user_info, "db_password")

    if not db_user or not db_password:
        username = user_info.get("preferred_username", "unknown")
        logger.error(f"MSSQL credentials not found for user {username}. user_info keys: {list(user_info.keys())}")
        raise Exception(f"MSSQL credentials not found in Keycloak user profile for {username}")

    return db_user, db_password

def get_connection_from_token(access_token: str, db_key: str = "DB1"):
    """
    Establish a database connection using Keycloak user's credentials.
    - Validates token with Keycloak
    - Extracts db_user and db_password from user attributes
    - Overrides .env credentials with user-specific ones
    - Returns a pyodbc connection object
    """
    user_info = get_user_info_from_token(access_token)
    if not user_info:
        raise Exception("Invalid access token or failed to retrieve user info.")

    db_user, db_password = extract_db_credentials(user_info)

    username = user_info.get("preferred_username", "unknown")
    logger.info(f"Establishing DB connection for Keycloak user '{username}' to '{db_key}'")

    # Override default DB connection settings with user-specific credentials
    config_overrides = {
        "user": db_user,
        "password": db_password,
    }

    return get_db_connection_direct(db_key, config_overrides=config_overrides)
