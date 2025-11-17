# Secure Multi-Database MSSQL MCP Server with Keycloak Auth

## Overview
This project delivers a production-ready **Model Context Protocol (MCP)** server that brokers secure, per-user SQL Server access. It combines **FastMCP**, **pyodbc**, and **Keycloak** to authenticate users, pull their individual SQL Server credentials, auto-discover every database they can reach, and expose safe MCP tools for querying and modifying data from clients such as **Postman MCP**, **Claude**, **ChatGPT**, or any MCP-compliant agent.

## Architecture
```
          ┌──────────────┐        1. Login (username/password)
          │   Keycloak   │◄──────────────────────────────────┐
          └──────┬───────┘                                   │
                 │ 2. Access token + user attributes         │
                 ▼                                           │
         ┌──────────────────────┐                            │
         │   FastMCP Server     │ 3. list_all_databases()    │
         │  (server.py)         │──────────────┐             │
         └─────────┬────────────┘              │             │
                   │                           ▼             │
                   │                ┌────────────────────┐   │
4. MCP tools (query/insert/...)     │ SQL Server Cluster │◄──┘
                   │                └────────────────────┘
                   ▼
          MCP Clients / Postman
```

## Key Features
- **Keycloak user authentication** with confidential clients and per-user passwords.
- **Access token verification** before any tool executes.
- **Multi-database auto-discovery** via `list_all_databases`, filtering only user-owned DBs.
- **Secure credential isolation**: each user operates with their Keycloak-provided credentials.
- **Dynamic database selection**: all tools accept a `db_name` parameter so callers target any accessible database.
- **MCP tool suite**:
  - `mssql_query_tool`
  - `mssql_insert_tool`
  - `mssql_update_tool`
  - `mssql_delete_tool`
  - `mssql_schema_tool`

## Description
- Authenticates every CLI and MCP request through **Keycloak**.
- Reads **db_user**, **db_password**, **db_driver**, **db_server**, **db_port**, and any of `db_database | database | db_name | db | preferred_db | mssql_db` to determine a preferred DB.
- Runs **automatic discovery** to enumerate all SQL Server databases the user can reach, building credential entries for each.
- Lets MCP tool calls specify `db_name`, so clients can hop between databases without restarting the session.
- Ships actionable MCP tools for SELECT, INSERT, UPDATE, DELETE, and schema inspection.
- Tested with **Postman MCP**, **Claude MCP**, **ChatGPT MCP connector**, and custom MCP clients.

## Keycloak Setup
| Attribute        | Example Value                       | Required |
|------------------|-------------------------------------|----------|
| `db_driver`      | `ODBC Driver 18 for SQL Server`     | ✅       |
| `db_server`      | `localhost`                         | ✅       |
| `db_user`        | `sa`                                | ✅       |
| `db_port`        | `1433`                              | ✅       |
| `db_password`    | `********`                          | ✅       |
| `db_database`    | `SalesDB` (preferred default)       | Optional |
| `db_name/db/database/preferred_db/mssql_db` | alternate preferred DB names | Optional |

1. **Create a realm** (e.g., `mssql-mcp`) within Keycloak Admin Console.  
2. **Create a confidential client** (e.g., `mssql-mcp-server`) with Direct Access Grants enabled and record the client secret.  
3. **Assign attributes to users** under *Users → Attributes*, matching the table above. These attributes are injected into access tokens or fetched via the UserInfo endpoint.  
4. **Token validation**: the server uses `verify_token` to check signature, expiry, and audience on each tool invocation.
5. *(Optional screenshot placeholder)* – Capture the user attributes screen for easy onboarding.

## Database Auto-discovery
- `list_all_databases()` connects using the user’s credentials and enumerates databases, removing `master`, `tempdb`, `model`, and `msdb` to avoid system DBs.
- The server builds `state.DB_CREDS` in the format:
  ```
  {
    "<db_name>": {
      "db_user": "...",
      "db_password": "...",
      "db_server": "...",
      "db_port": "...",
      "db_driver": "...",
      "db_database": "<db_name>"
    }
  }
  ```
- If Keycloak supplies a preferred DB, it is inserted first and becomes the `default` entry; otherwise the first discovered DB is used.

## Installation
1. **Requirements**
   - Python 3.11+ (pyodbc + FastMCP tested)
   - SQL Server (local or remote) reachable with ODBC Driver 18
   - Keycloak 21+ with confidential client credentials
2. **Clone and prepare**
   ```bash
   git clone <repo_url>
   cd mssql-mcp
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Environment variables** (if needed) via `.env` or system env:
   ```
   KEYCLOAK_URL=http://localhost:8080
   KEYCLOAK_REALM=mssql-mcp
   KEYCLOAK_CLIENT_ID=mssql-mcp-server
   KEYCLOAK_CLIENT_SECRET=<secret>
   ```
   Database credentials live only in Keycloak user attributes, not in `.env`.

## Running the Server
1. `python server.py`
2. Follow the CLI prompt to enter Keycloak username/password.
3. On success, the CLI prints your access token and the full list of discovered databases, highlighting the default.
4. FastMCP starts in `streamable-http` mode (default `http://127.0.0.1:8080/mcp`) ready for MCP clients.

## MCP Tool Reference
Each tool expects authenticated sessions; `db_name` is optional and defaults to the preferred or first discovered database.

### mssql_query_tool
- **Description**: Execute arbitrary `SELECT` statements with optional parameters.
- **Arguments**:
  - `query` (str)
  - `params` (list or null)
  - `db_name` (str, optional)
- **Postman Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "mssql_query_tool",
    "arguments": {
      "query": "SELECT TOP 10 * FROM Employees WHERE Department = ?",
      "params": ["Sales"],
      "db_name": "SalesDB"
    }
  }
}
```

### mssql_insert_tool
- **Description**: Insert rows using a dictionary payload.
- **Arguments**:
  - `table` (str)
  - `data` (dict)
  - `db_name` (str, optional)
- **Postman Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "mssql_insert_tool",
    "arguments": {
      "table": "Employees",
      "data": {
        "FirstName": "Ada",
        "LastName": "Lovelace",
        "Department": "R&D"
      },
      "db_name": "SalesDB"
    }
  }
}
```

### mssql_update_tool
- **Description**: Update existing rows using a JSON condition and payload.
- **Arguments**:
  - `table` (str)
  - `data` (dict of column updates)
  - `condition` (dict describing filters)
  - `db_name` (str, optional)
- **Postman Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "mssql_update_tool",
    "arguments": {
      "table": "Employees",
      "data": { "Department": "Innovation" },
      "condition": { "EmployeeID": 42 },
      "db_name": "SalesDB"
    }
  }
}
```

### mssql_delete_tool
- **Description**: Delete rows with a JSON condition.
- **Arguments**:
  - `table` (str)
  - `condition` (dict)
  - `db_name` (str, optional)
- **Postman Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "mssql_delete_tool",
    "arguments": {
      "table": "Employees",
      "condition": { "EmployeeID": 99 },
      "db_name": "SalesDB"
    }
  }
}
```

### mssql_schema_tool
- **Description**: Retrieve table schema metadata (columns, types, nullability).
- **Arguments**:
  - `table_name` (str)
  - `db_name` (str, optional)
- **Postman Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "mssql_schema_tool",
    "arguments": {
      "table_name": "Employees",
      "db_name": "SalesDB"
    }
  }
}
```

## Postman & MCP Clients
1. Open Postman (or Claude/ChatGPT MCP clients) and create a new MCP connection pointing to `http://127.0.0.1:8080/mcp`.
2. Sign in through the CLI when prompted; the server keeps the session active for all subsequent tool calls.
3. Call any tool JSON as shown above; responses include execution status and result payloads.

## Support & Contributions
- Use GitHub Issues for feature requests or bug reports.
- Contributions welcome: fork, branch, add tests, and open a PR describing the change.

Enjoy building secure, multi-database automations with the **Secure Multi-Database MSSQL MCP Server with Keycloak Auth**!
