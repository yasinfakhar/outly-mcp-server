import asyncio
import json
import os
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP, Context


SERVER_NAME = "outlty-mcp"

# Environment variables
ENV_BASE_URL = os.getenv("OUTLY_MCP_API_BASE_URL", "https://internal-api.outlylabs.com")
ENV_API_KEY = os.getenv("OUTLY_MCP_API_KEY", "")
ENV_AUTH_HEADER = os.getenv("OUTLY_MCP_AUTH_HEADER", "X-API-Key")  # or "Authorization"

server = FastMCP(SERVER_NAME)


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
    """OutlyLabs Tool : Create a new user-defined API from user intend (a natural language description). It can combine multiple APIs to create a new API. e.g: "Create a new user API to get the weather in a city."

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
    """OutlyLabs Tool : Make a request to a user-defined API endpoint.

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


if __name__ == "__main__":
    # Run MCP over stdio
    main()
