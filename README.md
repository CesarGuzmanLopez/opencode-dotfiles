# OpenCode Personal Configuration

Directorio de configuración personal para [OpenCode](https://opencode.ai) — agente de IA para coding.

## Estructura

```
~/.config/opencode/
├── opencode.jsonc          # Configuración principal (agentes, MCPs, permisos)
├── tui.json                # Configuración de la TUI
├── setup.py                # Instalador autónomo (genera todo el entorno)
├── package.json            # Dependencias npm
├── plugins/                # Plugins TypeScript que extienden OpenCode
├── skills/                 # Skills markdown (17 skills)
├── mcp-servers/            # MCP servers custom (web-search-mcp)
└── node_modules/           # Dependencias npm instaladas
```

## Agentes (16)

| Agente | Modo | Descripción |
|--------|------|-------------|
| `plan` | read-only | Planning y análisis. Solo lee, no modifica. |
| `read` | read-only | Solo lectura. Sin bash, sin edición. |
| `yolo` | full | Modo directo. Sin preguntas, ejecución directa. |
| `coding` | full | Developer general. Escribe, debuga, refactoriza. |
| `coding-web` | full | Web developer. Frontend, backend, APIs, Playwright. |
| `build` | full | Build y compilation tasks. |
| `scientific-research` | full | Research académico: papers, compuestos, citas. |
| `project-research-science` | full | Research científico de proyectos. |
| `deep-research` | full | Research iterativo profundo (5 rondas). |
| `research-web` | full | Web research specialist. |
| `doc-scout` | read-only | Busca documentación técnica y APIs. |
| `fact-checker` | read-only | Verifica claims y encuentra fuentes primarias. |
| `code-reviewer` | read-only | Review de código. Solo analiza, no modifica. |
| `test-writer` | full | Escribe tests unitarios, integration, E2E. |
| `refactoring` | full | Refactorización con comby. |
| `compaction` | — | Compactador interno (sin tools). |

## Skills (16)

### Desarrollo

| Skill | Descripción | Para quién |
|-------|-------------|------------|
| `coding` | Instrucciones generales de coding. Workflow: read → plan → implement → ruff → test → commit. | coding, coding-web, build |
| `refactoring` | Refactorización segura con comby. Preserva comportamiento. | coding, coding-web, build, refactoring |
| `tdd` | Test-driven development: RED → GREEN → REFACTOR. | coding, coding-web, build |
| `test-writer` | Escribe tests unitarios, integration, E2E. Cubre edge cases y mocks. | coding, coding-web, build |
| `commit-message` | Genera mensajes de commit convencionales limpios desde git diff. | coding, coding-web, build |
| `systematic-debugging` | Debug metódico: reproducir → aislar → hipótesis → test → fix → verificar. | coding, coding-web, build |
| `code-reviewer` | Review de código: bugs, security, performance, code style. Read-only. | code-reviewer |
| `plan` | Planning y análisis. Senior tech lead mode. Read-only. | plan |

### Research

| Skill | Descripción | Para quién |
|-------|-------------|------------|
| `deep-research` | Research iterativo de 5 rondas. Scout → Dive → Iterate → Verify → Finalize. | deep-research, scientific-research |
| `scientific-research` | Research académico y de proyectos: arXiv, PubMed, Crossref, PubChem. Divide en sub-tasks. | scientific-research, deep-research |
| `scientific-computing` | Cálculos científicos con Python: sympy, scipy, pandas. | scientific-computing |
| `doc-scout` | Busca documentación técnica, APIs, librerías. | doc-scout, research-web |
| `fact-checker` | Verifica claims con 2+ fuentes independientes. | fact-checker |

### Utilidades

| Skill | Descripción | Para quién |
|-------|-------------|------------|
| `system-tools` | Referencia de CLI tools: rg, fd, bat, jq, comby, gnuplot, plotext. | Todos |
| `read` | Solo lectura. No modifica, no ejecuta comandos. | read |
| `yolo` | Modo directo. Sin preguntas, ejecución directa. | yolo |

## MCPs (10)

| MCP | Descripción | Uso |
|-----|-------------|-----|
| `playwright` | Navegador Chromium para automatización web. | testing, scraping, UI automation |
| `sequential-thinking` | Razonamiento paso a paso para problemas complejos. | Todos los agentes |
| `memory` | Memoria persistente de conocimiento (knowledge graph). | Todos los agentes |
| `context7` | Documentación versionada de librerías en tiempo real. Previene alucinaciones de APIs. | coding, coding-web, build |
| `web-search` | Búsqueda web multi-motor (Bing/DuckDuckGo) + extracción de contenido. | Todos los agentes research |
| `arxiv` | Papers científicos de arXiv. Download, read, semantic search. | scientific-research |
| `pdf` | Lectura y extracción de contenido de PDFs. | Todos |
| `git` | Operaciones Git: commits, branches, diffs. | Todos |
| `pubchem` | Compuestos químicos y datos farmacéuticos. | scientific-research |
| `sonarqube` | Análisis de código estático (calidad, bugs, security). | build, code-reviewer |

## Permisos por Agente

### Skills

| Agente | Skills permitidas |
|--------|-------------------|
| `yolo` | **TODAS (16)** |
| `coding` | coding, refactoring, test-writer, tdd, commit-message, systematic-debugging, system-tools |
| `coding-web` | coding, refactoring, test-writer, tdd, commit-message, systematic-debugging, system-tools |
| `build` | coding, refactoring, test-writer, tdd, commit-message, systematic-debugging, system-tools |
| `scientific-research` | scientific-research, scientific-computing, deep-research, system-tools |
| `deep-research` | scientific-research, scientific-computing, deep-research, system-tools |
| `research-web` | doc-scout, system-tools |
| `doc-scout` | doc-scout, system-tools |
| `fact-checker` | fact-checker, system-tools |
| `code-reviewer` | code-reviewer, system-tools |
| `test-writer` | test-writer, system-tools |
| `refactoring` | refactoring, system-tools |
| `read` | read, plan, code-reviewer, doc-scout, fact-checker, system-tools |
| `plan` | plan, system-tools |

### Tools MCP

| Agente | Tools habilitadas |
|--------|-------------------|
| `yolo` | context7_* |
| `coding` | ruff, comby-*, git_*, web-search_*, context7_*, verify-deps |
| `coding-web` | playwright_*, web-search_*, context7_*, comby-*, git_*, verify-deps |
| `build` | verify-deps, git_*, arxiv_*, pdf_*, playwright_*, memory_*, pubchem_*, web-search_*, context7_* |
| `scientific-research` | arxiv_*, pubchem_*, pdf_*, memory_*, playwright_*, web-search_*, context7_*, chart, bat, research-save, save-findings, load-findings |
| `deep-research` | arxiv_*, pubchem_*, pdf_*, memory_*, playwright_*, web-search_*, context7_*, chart, bat, research-save, save-findings, load-findings |
| `project-research-science` | arxiv_*, pubchem_*, pdf_*, web-search_*, playwright_*, memory_*, context7_*, chart, save-findings, load-findings |
| `research-web` | playwright_*, web-search_*, context7_*, chart, research-save, save-findings, load-findings |
| `doc-scout` | playwright_*, web-search_*, context7_*, chart, bat |
| `fact-checker` | web-search_*, playwright_*, context7_*, bat |
| `code-reviewer` | git_*, context7_*, verify-deps |
| `test-writer` | git_*, playwright_*, context7_*, verify-deps |
| `refactoring` | git_*, comby-*, context7_*, verify-deps, save-findings, load-findings |
| `plan` | context7_* |
| `read` | context7_* |

## Análisis de Redundancias

### Skills

| Par | Relación | Recomendación |
|-----|----------|---------------|
| `test-writer` vs `tdd` | Complementarios | **Mantener ambos** — test-writer escribe tests, tdd es la metodología |
| `coding` vs `refactoring` | Diferentes | **Mantener ambos** — coding es general, refactoring es específico |
| `code-reviewer` vs `fact-checker` | Diferentes | **Mantener ambos** — uno revisa código, otro verifica claims |
| `deep-research` vs `doc-scout` | Diferentes | **Mantener ambos** — deep-research es iterativo, doc-scout busca docs |
| `plan` vs `read` | Diferentes | **Mantener ambos** — plan es análisis, read es solo lectura |

### MCPs

| MCP | Uso | Recomendación |
|-----|-----|---------------|
| `pubchem` | Química/farmacéutica | ⚠️ **Muy nicho** — eliminar si no haces research químico |
| `arxiv` | Papers científicos | ⚠️ **Nicho** — eliminar si no haces research académico |
| `sonarqube` | Calidad de código | ⚠️ **Requiere Docker** — eliminar si no tienes SonarQube corriendo |
| `pdf` | Lectura de PDFs | ✅ **Útil** — complementa web-search para docs offline |
| `git` | Operaciones Git | ✅ **Esencial** — pero ya tienes git_* en las tools |
| `context7` | Doc versionada | ✅ **Esencial** — previene alucinaciones de APIs |

### Resumen de candidatos a eliminar

```
MCPs candidatos a eliminar:
  ❌ pubchem    — Solo química. Muy nicho.
  ❌ arxiv      — Solo papers. Muy nicho.
  ❌ sonarqube  — Requiere Docker + SonarQube corriendo.

Skills candidatos a fusionar:
  ⚠️ scientific-research + project-research-science → fusionar en uno solo
```

## Instalación

### Rápida

```bash
python3 setup.py --target ~/.config/opencode
```

### Con parámetros

```bash
# Instalar en ruta específica
python3 setup.py --target ~/mi-opencode

# Con API key
python3 setup.py --api-key "tu-key"

# Omitir partes
python3 setup.py --skip-npm --skip-system
```

### Manual

```bash
cd ~/.config/opencode
npm install
```

## Plugins (8)

| Plugin | Herramienta | Descripción |
|--------|-------------|-------------|
| `bat` | `bat` | Muestra archivos con syntax highlighting |
| `comby` | `comby-search`, `comby-replace` | Búsqueda/reemplazo estructural de código |
| `plotext` | `chart` | Genera gráficas en terminal con plotext |
| `ruff` | `ruff` | Lint/format Python con ruff |
| `verify-deps` | `verify-deps` | Verifica dependencias del sistema |
| `verify-opencode` | `verify-opencode` | Verifica configuración de opencode |
| `research-save` | `research-save` | Guarda reportes de research |
| `save-findings` | `save-findings`, `load-findings` | Guarda/carga findings de research |

## Configuración

### opencode.jsonc

Archivo principal con:
- **Provider**: guzman-lopez (modelos: pensamiento-profundo, tareas-avanzadas, normal, vision, flash, compactador)
- **Agentes**: 16 agentes con permisos específicos
- **MCPs**: 10 servidores MCP
- **LSP**: TypeScript + Python
- **Permisos**: Global + por agente

### Cambios recientes

- Eliminado `brave-search` MCP (reemplazado por `web-search`)
- Agregado `context7` MCP a todos los agentes
- 5 skills eliminadas (admin, docs-writer, plugin-creator, project-research-code, security-auditor)
- 3 skills nuevas (commit-message, systematic-debugging, tdd)
- Skills actualizadas para usar `web-search` en vez de `duckduckgo`/`fetch`
- Fusionadas `scientific-research` + `project-research-science` en una sola skill

## License

Configuración personal; sin licencia específica.
