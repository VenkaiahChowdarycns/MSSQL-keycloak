# state.py

# Shared global state for the MCP server
logged_in_user = None
ACCESS_TOKEN = None
DB_CREDS = {}     # { dbname: {... credentials ... } }