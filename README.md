# OpenCode Personal Configuration

Directorio de configuración personal para [OpenCode](https://opencode.ai) — agente de IA para coding.

## Estructura

```
~/.config/opencode/
├── opencode.jsonc              # Configuración principal (GITIGNORED — contiene API keys)
├── opencode.template.jsonc     # Template portable para generar opencode.jsonc vía setup.py
├── tui.json                    # Configuración de la TUI
├── setup.py                    # Instalador autónomo (genera todo el entorno desde cero)
├── package.json                # Dependencias npm (MCP servers)
├── plugins/                    # Plugins TypeScript que extienden OpenCode (8 plugins)
├── skills/                     # Skills markdown (15 skills)
├── bin/                        # Scripts auxiliares (wrappers, MCPs custom)
│   ├── searxng-mcp.py          # MCP server para SearXNG (búsqueda web privada)
│   ├── searxng-mcp.sh          # Wrapper que carga .env y ejecuta el MCP
│   └── sonarqube-mcp-wrapper.sh# Wrapper para SonarQube MCP (GITIGNORED — contiene token)
├── hooks/                      # Git hooks (pre-commit con detección de secrets)
├── mcp/                        # Config de MCP servers
├── memory/                     # Memoria persistente (knowledge graph)
├── research/                   # Investigaciones guardadas
└── themes/                     # Temas (pendiente)
```

## Agentes (11)

| Agente | Modo | Descripción |
|--------|------|-------------|
| `plan` | read-only | Planning y análisis. Solo lee, no modifica archivos. |
| `read` | read-only | Solo lectura. Sin bash, sin edición, sin task. |
| `research` | full | Investigación: web, papers, compuestos, documentación. |
| `coding` | full | Developer general. Escribe, debuga, refactoriza. |
| `coding-web` | full | Web developer. Frontend, backend, APIs, Playwright. |
| `code-quality` | full | Code review, testing, refactoring, SonarQube. |
| `build` | full | Build y compilation tasks. |
| `refactoring` | full | Refactorización estructural con comby. |
| `typescript-dev` | full | TypeScript/JavaScript, Node.js, React, Next.js. |
| `rust-dev` | full | Rust, Cargo, sistemas. |
| `cpp-dev` | full | C/C++, CMake, sistemas. |

> 📖 Ver [agents.md](./agents.md) para documentación detallada de cada agente.

## Skills (15)

### Desarrollo

| Skill | Descripción | Agentes |
|-------|-------------|---------|
| `coding` | Instrucciones generales de coding. Workflow: read → plan → implement → ruff → test → commit. | coding, coding-web, build, typescript-dev, rust-dev, cpp-dev |
| `refactoring` | Refactorización segura con comby. Preserva comportamiento. | coding, coding-web, build, refactoring |
| `tdd` | Test-driven development: RED → GREEN → REFACTOR. | coding, coding-web, build |
| `test-writer` | Escribe tests unitarios, integration, E2E. | coding, coding-web, build, code-quality |
| `commit-message` | Genera mensajes de commit convencionales desde git diff. | coding, coding-web, build |
| `systematic-debugging` | Debug metódico: reproducir → aislar → hipótesis → test → fix. | coding, coding-web, build |
| `code-reviewer` | Review de código: bugs, security, performance. Read-only. | code-quality |

### Research

| Skill | Descripción | Agentes |
|-------|-------------|---------|
| `deep-research` | Research iterativo de 5 rondas (Scout → Dive → Iterate → Verify → Finalize). | research |
| `scientific-research` | Research académico: arXiv, PubChem, papers. | research |
| `scientific-computing` | Cálculos científicos con Python (sympy, scipy, pandas). | research |
| `doc-scout` | Busca documentación técnica, APIs, librerías. | research |
| `fact-checker` | Verifica claims con 2+ fuentes independientes. | research |

### Utilidades

| Skill | Descripción | Agentes |
|-------|-------------|---------|
| `system-tools` | Referencia de CLI tools: rg, fd, bat, jq, comby, plotext. | Todos |
| `plan` | Planning y análisis. Senior tech lead mode. Read-only. | plan |
| `read` | Solo lectura. No modifica, no ejecuta comandos. | read |

## MCPs (11)

| MCP | Descripción | Tecnología |
|-----|-------------|------------|
| `playwright` | Navegador Chromium para automatización web. | npm |
| `sequential-thinking` | Razonamiento paso a paso para problemas complejos. | npm |
| `memory` | Memoria persistente (knowledge graph en JSON). | npm |
| `context7` | Documentación versionada de librerías en tiempo real. | npm |
| `web-search` | Búsqueda web multi-motor via SearXNG privado. | Python |
| `arxiv` | Papers científicos de arXiv (download, read, semantic search). | Python (uv) |
| `pdf` | Lectura y extracción de contenido de PDFs. | npm |
| `git` | Operaciones Git (commits, branches, diffs). | npm |
| `pubchem` | Compuestos químicos y datos farmacéuticos. | npm |
| `sonarqube` | Análisis de código estático (calidad, bugs, security). | npm |
| `memos` | Servicio de notas y memos (remoto). | remote (HTTP) |

## Plugins (8)

| Plugin | Herramienta | Descripción |
|--------|-------------|-------------|
| `bat` | `bat` | Muestra archivos con syntax highlighting |
| `comby` | `comby-search`, `comby-replace` | Búsqueda/reemplazo estructural de código |
| `plotext` | `chart` | Genera gráficas en terminal con plotext |
| `ruff` | `ruff` | Lint/format Python con ruff |
| `verify-deps` | `verify-deps` | Verifica dependencias del sistema |
| `verify-opencode` | `verify-opencode` | Verifica configuración de opencode |
| `research-save` | `research-save` | Guarda reportes de investigación |
| `save-findings` | `save-findings`, `load-findings` | Guarda/carga findings de investigación |

## LSPs

| Lenguaje | Servidor LSP | Extensiones |
|----------|-------------|-------------|
| TypeScript/JavaScript | `typescript-language-server` | .ts, .tsx, .js, .jsx, .mjs, .cjs, .mts, .cts |
| Python | `pylsp` | .py, .pyi |
| C/C++ | `clangd` | .cpp, .cxx, .cc, .c, .h, .hpp, .hxx |
| Rust | `rust-analyzer` | .rs |

## Proveedor LLM

- **Provider:** `guzman-lopez` (API compatible con OpenAI)
- **Base URL:** `https://llm.guzman-lopez.com/v1`
- **Modelo default:** `normal-gratis`
- **Modelos disponibles:**
  - `pensamiento-profundo-caro` — Pensamiento Profundo (tools, vision, streaming)
  - `tareas-avanzadas` — Tareas Avanzadas (tools, vision, streaming)
  - `normal` — Normal (tools, vision, streaming)
  - `normal-gratis` — Normal Gratis (default)
  - `vision` — Visión (tools, vision, sin parallel_tool_calls)
  - `flash` — Flash (tools, vision, sin parallel_tool_calls)
  - `compactador` — Compactador (sin tools, solo texto/visión)

## Instalación

```bash
# Desde cero en cualquier sistema
python3 setup.py --target ~/.config/opencode

# Con API key
python3 setup.py --api-key "tu-key"

# Omitir partes (ya instaladas)
python3 setup.py --skip-npm --skip-system --skip-python

# Solo dependencias npm
cd ~/.config/opencode && npm install
```

## Licencia

Configuración personal; sin licencia específica.
