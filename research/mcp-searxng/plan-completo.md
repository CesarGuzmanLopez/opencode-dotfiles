---
filename: plan-completo.md
date: 2026-06-07
---

# MCP SearXNG - Plan Completo

## Estado actual
- DuckDuckGo MCP (mcp-duckduckgo v2.0.0): busqueda + crawl + research
- websearch nativo: Exa/Parallel sin API keys (no funciona)
- Proxy 127.0.0.1:7890 bloqueando busquedas

## Solucion
Usar mcp-searxng-enhanced (Python, 50 stars, MIT) + deteccion inteligente de framework/anti-bot.

## Repos existentes evaluados
- OvertliDS/mcp-searxng-enhanced (50 stars) - Python - Scraping con Trafilatura - BAJA complejidad - GANADOR
- luxiaolei/searxng-crawl4ai-mcp (27 stars) - TypeScript - Scraping con Crawl4AI+Playwright - ALTA complejidad (Docker+Redis)
- SecretiveShell/MCP-searxng (118 stars) - Python - Sin scraping - MINIMA complejidad
- jae-jae/searxng-mul-mcp (99 stars) - TypeScript - Multi-query parallel

## Fases del plan
1. Instalar MCP existente (clonar repo + pip install + configurar URL SearXNG)
2. Crear scrape_detector.py (HTTP GET ligero + deteccion HTML)
3. Integrar detector en mcp_server.py (campo scrape_hint en resultados)
4. Configurar MCP en opencode.jsonc (eliminar web-search, agregar searxng)
5. Eliminar lo viejo (npm uninstall mcp-duckduckgo)
6. Actualizar permisos y tools en agentes (web-search_* a searxng_*)
7. Actualizar skills (doc-scout, fact-checker)
8. Verificacion (reiniciar, probar search, probar scrape_hint)

## Deteccion inteligente - senales
- Cloudflare (cf-browser-verification, cf-challenge) -> Playwright
- reCAPTCHA/hCaptcha -> Playwright
- Next.js (__NEXT_DATA__) -> Playwright
- Angular (ng-version, app-root) -> Playwright
- React SPA (div root vacio) -> Playwright
- Vue/Nuxt (__NUXT__, data-vue) -> Playwright
- HTML estatico (contenido visible sin JS) -> webfetch

## Tools del MCP final
- searxng_search: busqueda web + deteccion scraping
- searxng_get_website: scraping directo de URL
- searxng_get_current_datetime: fecha/hora actual

## Stack final
- SearXNG (servidor): motor de busqueda multi-engine
- mcp-searxng-enhanced: MCP server con search + scraping + deteccion
- webfetch: contenido paginas estaticas
- Playwright: JS, SPAs, anti-bot

## Notas pendientes
- El usuario NO proporciono la URL de su servidor SearXNG
- Verificar si el proxy 127.0.0.1:7890 afecta al MCP
- No se necesita Docker (ejecucion nativa con Python)