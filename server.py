import asyncio
import json
import os
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP, Context


SERVER_NAME = "outlty-mcp"

OUTLY_MCP_INSTRUCTIONS = """You are connected to Outly's MCP server.

This server provides tools to:
- Discover existing user-defined APIs (tools) that Outly has already created.
- Generate new user-defined APIs (new callable routes) when you need a capability that does not exist yet.
- Execute those generated APIs with the required JSON inputs.

Dynamic tool/route generation workflow:
1) If you need to perform an action and there is no suitable tool available, call `create_user_api` with a clear natural language description of the desired API.
   Include:
   - expected inputs (fields + types + constraints)
   - expected outputs (shape + examples)
   - any external APIs/services that should be used
2) If execution requires authentication for upstream gateways, call `generate_auth_links` for the created API and ask the user to complete authentication.
3) Call the API using `make_request` with the API's `url` and an `input_data` JSON body matching the API's input schema.

Notes:
- Prefer using existing APIs via `list_user_apis` / `get_user_api` before generating a new one.
- Only request a new API when necessary; keep APIs minimal, deterministic, and well-scoped.
"""

# Environment variables
ENV_BASE_URL = os.getenv("OUTLY_MCP_API_BASE_URL", "https://internal-api.outlylabs.com")
ENV_API_KEY = os.getenv("OUTLY_MCP_API_KEY", "")
ENV_AUTH_HEADER = os.getenv("OUTLY_MCP_AUTH_HEADER", "X-API-Key")  # or "Authorization"

server = FastMCP(SERVER_NAME, instructions=OUTLY_MCP_INSTRUCTIONS)


def _auth_headers(api_key: Optional[str] = None, header_name: Optional[str] = None) -> Dict[str, str]:
    """Build authentication headers expected by the FastAPI backend.

    Defaults to sending X-API-Key: <key>. The backend also supports
    Authorization: ApiKey <key> if OUTLY_MCP_AUTH_HEADER is set to "Authorization".
    """
    key = (api_key or ENV_API_KEY).strip()
    name = (header_name or ENV_AUTH_HEADER).strip()
    if not key:
        raise ValueError("OUTLY_MCP_API_KEY is not set")
    if name.lower() == "authorization":
        return {"Authorization": f"ApiKey {key}"}
    return {name: key}


async def _client() -> httpx.AsyncClient:
    """Create a shared AsyncClient with reasonable timeouts."""
    timeout = httpx.Timeout(20.0, read=60.0)
    return httpx.AsyncClient(timeout=timeout)


def main() -> None:
    """Console entry point to run the MCP server over stdio."""
    server.run()


@server.tool()
async def list_user_apis(ctx: Context) -> Any:
    """OutlyLabs Tool : List previous user-defined APIs.

    Returns:
      List of user APIs.
    """
    url = f"{ENV_BASE_URL.rstrip('/')}/api-key/user-apis"
    headers = _auth_headers()
    async with await _client() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


@server.tool()
async def get_user_api(ctx: Context, id: str) -> Any:
    """OutlyLabs Tool : Get details of a single user API by ID.

    Args:
      id: UUID string of the user API.

    Returns:
      Details of the user API including name, description, URL, and input/output schema.
    """
    url = f"{ENV_BASE_URL.rstrip('/')}/api-key/user-apis/{id}"
    headers = _auth_headers()
    async with await _client() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


@server.tool()
async def create_user_api(ctx: Context, user_query: str) -> Any:
    """OutlyLabs Tool : Create a new user-defined API from user intend (a natural language description). You can specify the expected input and output. It can combine multiple APIs to create a new API. e.g: "Create a new user API to return weather summary for a given city name."

    Args:
      user_query: Natural language description of the API to create.

    Returns:
      Details of the created user API including name, description, URL, and input/output schema.
    """
    url = f"{ENV_BASE_URL.rstrip('/')}/api-key/user-apis"
    headers = _auth_headers()
    payload = {"user_query": user_query}
    async with await _client() as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


@server.tool()
async def make_request(ctx: Context, url: str, input_data: Dict[str, Any]) -> Any:
    """OutlyLabs Tool : Make a request to a user-defined API endpoint. **Important** : before calling a route it should be authenticated so first call 'generate_auth_links' and ask user to authenticate to all links then call the route.

    Args:
      url: The executable API URL (it can be get from detail of user defined API in outlylabs tools).
      input_data: The JSON body to send to that API.

    Returns:
      Response from the endpoint.
    """
    backend_url = f"{ENV_BASE_URL.rstrip('/')}/api-key/user-apis/make-request"
    headers = _auth_headers()
    payload = {"url": url, "input_data": input_data}
    async with await _client() as client:
        resp = await client.post(backend_url, headers=headers, json=payload)
        resp.raise_for_status()
        # Backend returns JSON or raw text wrapped in {"raw": ...}
        return resp.json()


@server.tool()
async def generate_auth_links(ctx: Context, user_api_id: str) -> Any:
    """OutlyLabs Tool : Generate auth links for all gateways requiring authentication inside of a user API. If the reutrend list is empty means this route has no authentication

    Args:
      user_api_id: UUID string of the user API.

    Returns:
      Auth link payload including the user_api_id and the list of gateway auth links.
    """
    url = (
        f"{ENV_BASE_URL.rstrip('/')}/api-key/user-apis/{user_api_id}/gateway-auth/links"
    )
    headers = _auth_headers()
    async with await _client() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    # Run MCP over stdio
    main()
