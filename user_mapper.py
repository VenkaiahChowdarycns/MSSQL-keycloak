import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAPPING_FILE = Path(__file__).parent / "user_folder_mapping.json"

def load_user_mappings() -> dict:
    """Load user-to-folder mappings from JSON file."""
    try:
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded user mappings from {MAPPING_FILE}")
        return data
    except FileNotFoundError:
        logger.error(f"Mapping file not found: {MAPPING_FILE}")
        return {"users": []}

def get_user_mapping(keycloak_username: str) -> dict:
    """
    Retrieve folder and DB access mapping for a Keycloak user.
    Returns: { keycloak_username, folders, db_user, db_access_level, found }
    """
    mappings = load_user_mappings()
    for user in mappings.get("users", []):
        if user.get("keycloak_username") == keycloak_username:
            return {
                "found": True,
                "keycloak_username": user.get("keycloak_username"),
                "folders": user.get("folders", []),
                "db_user": user.get("db_user"),
                "db_access_level": user.get("db_access_level", "read_only"),
            }
    
    logger.warning(f"No mapping found for user: {keycloak_username}")
    return {
        "found": False,
        "keycloak_username": keycloak_username,
        "folders": [],
        "db_user": None,
        "db_access_level": "none",
    }

def authorize_user_for_query(keycloak_username: str, operation: str = "read") -> bool:
    """
    Check if user is authorized for a specific operation (read, write, delete).
    Returns: True if authorized, False otherwise.
    """
    mapping = get_user_mapping(keycloak_username)
    if not mapping.get("found"):
        logger.warning(f"User {keycloak_username} not found in mappings")
        return False
    
    access_level = mapping.get("db_access_level", "none")
    
    if operation == "read":
        return access_level in ("read_only", "read_write")
    elif operation == "write":
        return access_level == "read_write"
    elif operation == "delete":
        return access_level == "read_write"
    
    return False
