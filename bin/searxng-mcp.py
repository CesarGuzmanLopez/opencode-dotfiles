#!/usr/bin/env python3
"""
MCP Server for SearXNG — Private search engine.
Reads credentials from environment variables:
  SEARXNG_URL, SEARXNG_USER, SEARXNG_PASS

Protocol: MCP stdio transport (JSON-RPC over stdin/stdout)
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import base64
import ssl

# ── Config ────────────────────────────────────────────────────────────────
SEARXNG_URL = os.environ.get("SEARXNG_URL", "https://sear.guzman-lopez.com")
SEARXNG_USER = os.environ.get("SEARXNG_USER", "")
SEARXNG_PASS = os.environ.get("SEARXNG_PASS", "")

# ── Helpers ───────────────────────────────────────────────────────────────

def _auth_header():
    token = base64.b64encode(f"{SEARXNG_USER}:{SEARXNG_PASS}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _search_searxng(query, limit=10):
    """Query SearXNG JSON API and return parsed results."""
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "language": "es",
        "categories": "general",
        "pageno": 1,
    })
    url = f"{SEARXNG_URL}/search?{params}"

    req = urllib.request.Request(url, headers=_auth_header())
    # Allow self-signed certs if needed
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e), "results": []}

    results = []
    for r in data.get("results", [])[:limit]:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "engine": r.get("engine", ""),
            "engines": r.get("engines", []),
            "score": r.get("score", 0),
            "publishedDate": r.get("publishedDate"),
            "category": r.get("category", ""),
        })
    return {"query": data.get("query", query), "results": results, "total": len(results)}


def _fetch_url(url, timeout=10):
    """Fetch content from a URL."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; SearXNG-MCP/1.0)"
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            # Strip HTML tags roughly
            import re
            text = re.sub(r"<[^>]+>", " ", content)
            text = re.sub(r"\s+", " ", text).strip()
            return {"url": url, "content": text[:5000], "status": resp.status}
    except Exception as e:
        return {"url": url, "error": str(e), "content": ""}


# ── MCP Protocol ──────────────────────────────────────────────────────────

def _send(msg):
    """Send a JSON-RPC message to stdout (MCP stdio transport)."""
    line = json.dumps(msg, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _handle_request(msg):
    """Process a JSON-RPC request/message."""
    method = msg.get("method", "")
    msg_id = msg.get("id")
    params = msg.get("params", {})

    # ── initialize ──
    if method == "initialize":
        _send({
            "jsonrpc": "2.0", "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "search": {
                            "description": "Search the web using SearXNG private search engine",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Search query"},
                                    "limit": {"type": "number", "description": "Max results (1-50)", "default": 10}
                                },
                                "required": ["query"]
                            }
                        },
                        "search_and_crawl": {
                            "description": "Search and crawl full content from results",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Search query"},
                                    "limit": {"type": "number", "description": "Max results to crawl (1-5)", "default": 3}
                                },
                                "required": ["query"]
                            }
                        },
                        "research": {
                            "description": "Deep research: search, crawl, and rank results",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Research question"},
                                    "count": {"type": "number", "description": "Number of sources (1-8)", "default": 5}
                                },
                                "required": ["query"]
                            }
                        }
                    }
                },
                "serverInfo": {"name": "searxng-mcp", "version": "1.0.0"}
            }
        })
        return

    # ── tools/list ──
    if method == "tools/list":
        _send({
            "jsonrpc": "2.0", "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "search",
                        "description": "Search the web using SearXNG private search engine (Google, DuckDuckGo, Brave, Qwant, etc.)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "limit": {"type": "number", "description": "Max results (1-50)", "default": 10}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "search_and_crawl",
                        "description": "Search the web and crawl the full content of each result page",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "limit": {"type": "number", "description": "Max results to crawl (1-5)", "default": 3}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "research",
                        "description": "Deep research: search, crawl content, and rank results by relevance",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Research question"},
                                "count": {"type": "number", "description": "Number of sources (1-8)", "default": 5}
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        })
        return

    # ── tools/call ──
    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        result = None

        if tool_name == "search":
            query = tool_args.get("query", "")
            limit = min(int(tool_args.get("limit", 10)), 50)
            data = _search_searxng(query, limit)
            text = f"# Búsqueda: {data['query']}\n\n"
            for i, r in enumerate(data["results"], 1):
                text += f"## {i}. {r['title']}\n"
                text += f"**URL:** {r['url']}\n"
                text += f"**Resumen:** {r['content']}\n"
                text += f"**Motores:** {', '.join(r['engines'])} | **Score:** {r['score']}\n\n"
            text += f"---\n*Total: {data['total']} resultados*"
            result = text

        elif tool_name == "search_and_crawl":
            query = tool_args.get("query", "")
            limit = min(int(tool_args.get("limit", 3)), 5)
            data = _search_searxng(query, limit)
            text = f"# Búsqueda + Crawl: {data['query']}\n\n"
            for i, r in enumerate(data["results"], 1):
                text += f"## {i}. {r['title']}\n"
                text += f"**URL:** {r['url']}\n"
                text += f"**Resumen:** {r['content']}\n"
                crawled = _fetch_url(r["url"])
                if crawled.get("content"):
                    text += f"**Contenido completo:**\n{crawled['content'][:2000]}\n\n"
                else:
                    text += f"**Error al scrapear:** {crawled.get('error', 'desconocido')}\n\n"
            result = text

        elif tool_name == "research":
            query = tool_args.get("query", "")
            count = min(int(tool_args.get("count", 5)), 8)
            data = _search_searxng(query, count)
            text = f"# Investigación: {data['query']}\n\n"
            crawled_results = []
            for r in data["results"]:
                crawled = _fetch_url(r["url"])
                crawled_results.append({**r, "full_content": crawled.get("content", "")[:2000]})
            for i, r in enumerate(crawled_results, 1):
                text += f"## {i}. {r['title']}\n"
                text += f"**URL:** {r['url']}\n"
                text += f"**Resumen:** {r['content']}\n"
                if r["full_content"]:
                    text += f"**Detalle:**\n{r['full_content'][:1000]}\n\n"
            text += f"---\n*Fuentes analizadas: {len(crawled_results)}*"
            result = text

        else:
            _send({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}})
            return

        _send({
            "jsonrpc": "2.0", "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": result or "Sin resultados"}]
            }
        })
        return

    # ── ping ──
    if method == "ping":
        _send({"jsonrpc": "2.0", "id": msg_id, "result": {}})
        return

    # ── notifications (no response) ──
    if "id" not in msg:
        return

    _send({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})


# ── Main loop ─────────────────────────────────────────────────────────────

def main():
    # The MCP protocol requires the client to send "initialize" first.
    # The server responds with capabilities — do NOT send anything proactively.
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            _handle_request(msg)
        except json.JSONDecodeError as e:
            # Ignore malformed messages
            pass
        except Exception as e:
            try:
                _send({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}})
            except Exception:
                pass


if __name__ == "__main__":
    main()
