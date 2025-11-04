#  Microsoft SQL MCP Tool Server

This project provides a **Model Context Protocol (MCP)** server for interacting with **Microsoft SQL Server (MSSQL)**.  
It uses [`fastmcp`] as the MCP server framework and exposes tools for common database operations such as:

- Running SQL queries  
- Inserting rows  
- Updating data  
- Deleting records  
- Checking database health  
- Getting table schema details  

---

## Features

- ✅ Execute any valid MSSQL query  
- ✅ Insert, update, and delete records dynamically  
- ✅ Retrieve table schema and metadata  
- ✅ Check database connection health  
- ✅ Designed for real-time MCP interaction  
- ✅ Works seamlessly with **Postman MCP**, or any MCP-compatible client  

---

## Python Version Dependencies

- **Working**: Python 3.14


## Installation

1. **Clone the repository and navigate into it:**

   ```bash
   git clone <repo_url>
   cd mssql-mcp-server
   ```
2. **Create a virtual environment:**
```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. **Install dependencies:**
```bash
pip install -r requirements.txt
```
##  **Project Structure**
```bash
mssql-mcp-server/
├── server.py
├── db.py
├── tools/
│   ├── mssql_query.py
│   ├── mssql_insert.py
│   ├── mssql_update.py
│   ├── mssql_delete.py
│   ├── mssql_schema.py
│   
├── .env
└── requirements.txt
```

# MSSQL Connection Configuration
```bash
MSSQL_SERVER=localhost
MSSQL_DATABASE=YourDatabaseName
MSSQL_USER=YourUsername
MSSQL_PASSWORD=YourPassword
MSSQL_DRIVER=ODBC Driver 17 for SQL Server
```
## Available MCP Tools

| Tool Name | Description | Parameters |
| --------- | ----------- | ---------- |
| `insert` | Execute any custom SQL query | `table: str, data: [str, Any]` |
| `update` | Update existing data | `table: str, data: [str, Any], condition: [str, Any]` |
| `query` | Execute any custom SQL query  | `query: str, params: Optional[List[Any]]` |
| `delete` | Delete records from a table | `table: str, condition: [str, Any]` |
| `schema` | Retrieve schema of a specific table | `table_name: str` |


##  Running the MCP Server 

```bash
python server.py
```
the server will run using streamable-http transport at:

```bash
http://127.0.0.1:8080
```

## Testing with Postman

1. Open Postman (latest version with MCP support).
2. Click New → MCP Request.
3. Enter the MCP server URL:
 ```bash
http://127.0.0.1:8080/mcp
```
4. Click Connect.
5. You will now see all available tools (mssql_query_tool, mssql_insert_tool, mssql_update_tool, mssql_delete_tool, mssql_schema_tool, mssql_health_tool) listed automatically in the Messages block.
6. Select a tool and provide the required input arguments.
7. Run the request — you will get a live response from your connected Microsoft SQL Server.

No need to craft raw JSON manually — Postman MCP automatically lists and formats available tools for you.

