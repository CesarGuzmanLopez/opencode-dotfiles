# Python MCP Server Implementation Guide

## Overview

This document provides Python-specific best practices and examples for implementing MCP servers using the MCP Python SDK (FastMCP). It covers server setup, tool registration patterns, input validation with Pydantic, error handling, and complete working examples.

---

## Quick Reference

### Key Imports
```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
import httpx
```

### Server Initialization
```python
mcp = FastMCP("service_mcp")
```

### Tool Registration Pattern
```python
@mcp.tool(name="tool_name", annotations={...})
async def tool_function(params: InputModel) -> str:
    # Implementation
    pass
```

---

## MCP Python SDK and FastMCP

FastMCP provides:
- Automatic description and inputSchema generation from function signatures and docstrings
- Pydantic model integration for input validation
- Decorator-based tool registration with `@mcp.tool`

## Server Naming Convention

Python MCP servers use format `{service}_mcp` (lowercase with underscores):
- Examples: `github_mcp`, `jira_mcp`, `stripe_mcp`

## Tool Implementation

### Tool Naming
Use snake_case with service prefix: `slack_send_message`, `github_create_issue`

### Tool Structure with FastMCP

```python
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example_mcp")

class ServiceToolInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    param1: str = Field(..., description="First parameter", min_length=1, max_length=100)
    param2: Optional[int] = Field(default=None, description="Optional parameter", ge=0, le=1000)

@mcp.tool(
    name="service_tool_name",
    annotations={
        "title": "Human-Readable Tool Title",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def service_tool_name(params: ServiceToolInput) -> str:
    '''Tool description.

    Args:
        params (ServiceToolInput): Validated input parameters

    Returns:
        str: JSON-formatted response containing operation results
    '''
    pass
```

## Pydantic v2 Key Features

- Use `model_config` instead of nested `Config` class
- Use `field_validator` instead of deprecated `validator`
- Use `model_dump()` instead of deprecated `dict()`

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict

class CreateUserInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    name: str = Field(..., description="User's full name", min_length=1, max_length=100)
    email: str = Field(..., description="Email address", pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Email cannot be empty")
        return v.lower()
```

## Response Format Options

```python
from enum import Enum

class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"

class UserSearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )
```

## Pagination Implementation

```python
class ListInput(BaseModel):
    limit: Optional[int] = Field(default=20, description="Max results", ge=1, le=100)
    offset: Optional[int] = Field(default=0, description="Results to skip", ge=0)

async def list_items(params: ListInput) -> str:
    data = await api_request(limit=params.limit, offset=params.offset)
    response = {
        "total": data["total"],
        "count": len(data["items"]),
        "offset": params.offset,
        "items": data["items"],
        "has_more": data["total"] > params.offset + len(data["items"]),
    }
    import json
    return json.dumps(response, indent=2)
```

## Error Handling

```python
def _handle_api_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 404:
            return "Error: Resource not found."
        elif e.response.status_code == 403:
            return "Error: Permission denied."
        elif e.response.status_code == 429:
            return "Error: Rate limit exceeded."
        return f"Error: API request failed with status {e.response.status_code}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out."
    return f"Error: Unexpected error: {type(e).__name__}"
```

## Shared Utilities

```python
async def _make_api_request(endpoint: str, method: str = "GET", **kwargs) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method, f"{API_BASE_URL}/{endpoint}", timeout=30.0, **kwargs
        )
        response.raise_for_status()
        return response.json()
```

## Transport Options

```python
# stdio transport (for local tools) - default
if __name__ == "__main__":
    mcp.run()

# Streamable HTTP transport (for remote servers)
if __name__ == "__main__":
    mcp.run(transport="streamable_http", port=8000)
```

## Quality Checklist

- [ ] All tools have descriptive names and documentation
- [ ] All tools use Pydantic BaseModel for input validation with Field() definitions
- [ ] Annotations correctly set (readOnlyHint, destructiveHint, idempotentHint, openWorldHint)
- [ ] Error handling implemented for all external calls
- [ ] All network operations use async/await
- [ ] Common functionality extracted into reusable functions
- [ ] Pagination properly implemented where applicable
- [ ] Type hints used throughout the code
