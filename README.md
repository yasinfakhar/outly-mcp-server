# outlty-mcp

A Python MCP server exposing your FastAPI API-key routes as MCP tools for use in Claude Code (and any MCP client).

## Tools
- list_user_apis
- get_user_api
- create_user_api
- make_request

## Prerequisites
- Python 3.10+
- Your backend running and accessible (default base URL: http://localhost:8000)
- An API key valid for the backend. The backend supports either:
  - `X-API-Key: <key>`
  - `Authorization: ApiKey <key>`

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run with uvx (recommended)
You can run this server without a local install using uv.

Local checkout:
```bash
uvx --from . outlty-mcp
```

From Git repository (example):
```bash
uvx --from git+https://github.com/your-org/outly-mcp-server.git outlty-mcp
```

You can also pin a version published to an index:
```bash
uvx outlty-mcp
```

## Run (standalone debug)
This server communicates via stdio when launched by an MCP client, but you can validate it imports:
```bash
python server.py
```

## Configuration (env)
- `OUTLY_MCP_API_BASE_URL` (default: `http://localhost:8000`)
- `OUTLY_MCP_API_KEY` (required)
- `OUTLY_MCP_AUTH_HEADER` (default: `X-API-Key`; set to `Authorization` to send `Authorization: ApiKey <key>`)

## Claude Code configuration (JSON)
Add this to your Claude configuration (e.g., `~/.config/anthropic/claude_desktop_config.json` or the workspace `.claued.json` depending on your setup). See Claude docs for exact location.

```json
{
  "mcpServers": {
    "outlty-mcp": {
      "command": "uvx",
      "args": ["outlty-mcp"],
      "env": {
        "OUTLY_MCP_API_BASE_URL": "http://localhost:8000",
        "OUTLY_MCP_API_KEY": "ak_xxx_your_secret",
        "OUTLY_MCP_AUTH_HEADER": "X-API-Key"
      }
    }
  }
}
```

If you prefer Authorization header:
```json
{
  "mcpServers": {
    "outlty-mcp": {
      "command": "uvx",
      "args": ["outlty-mcp"],
      "env": {
        "OUTLY_MCP_API_BASE_URL": "http://localhost:8000",
        "OUTLY_MCP_API_KEY": "ak_xxx_your_secret",
        "OUTLY_MCP_AUTH_HEADER": "Authorization"
      }
    }
  }
}
```

## Tool schemas
- list_user_apis: GET `/api-key/user-apis`
- get_user_api(id: string): GET `/api-key/user-apis/{id}`
- create_user_api(user_query: string): POST `/api-key/user-apis`
- make_request(url: string, input_data: object): POST `/api-key/user-apis/make-request`
