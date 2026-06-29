# OpenCode Agents — Documentación Detallada

> 11 agentes configurados. Actualizado: Junio 2026.

---

## `plan` — Planning, Analysis & Documentation Research

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.1 (mínima creatividad, máxima precisión) |
| Read-only | Sí (edit: deny) |
| Prompt | *"You are a senior tech lead for planning and documentation research."* |

### Permisos

| Recurso | Acceso |
|---------|--------|
| Editar archivos | ❌ Denegado |
| Bash | ✅ Permitido |
| Lectura/Glob/Grep | ✅ Permitido |
| Task (subagentes) | ✅ Permitido |
| Web fetch / Web search | ✅ Permitido |
| LSP | ✅ Permitido |
| Question | ✅ Permitido |
| Doom loop | ✅ Permitido (sin confirmación) |

### Skills habilitadas
- `plan` — Planning y análisis
- `read` — Solo lectura
- `doc-scout` — Búsqueda de documentación
- `fact-checker` — Verificación de hechos
- `system-tools` — Referencia de herramientas CLI

### Tools exclusivas
- `memos_*` — Gestión de memos
- `sequential-thinking` — Razonamiento estructurado
- `memory_*` — Memoria persistente (knowledge graph)
- `context7_*` — Documentación de librerías
- `web-search_*` — Búsqueda web
- `arxiv_*` — Papers científicos
- `pdf_*` — Lectura de PDFs

### Casos de uso
- Analizar requisitos antes de codificar
- Investigar documentación de APIs
- Planificar arquitectura de proyectos
- Verificar hechos técnicos

---

## `read` — Pure Read-Only

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.1 |
| Read-only | Sí (edit: deny, bash: deny, task: deny) |
| Prompt | *"You are a read-only assistant."* |

### Permisos

| Recurso | Acceso |
|---------|--------|
| Editar archivos | ❌ Denegado |
| Bash | ❌ Denegado |
| Task (subagentes) | ❌ Denegado |
| Todo write | ❌ Denegado |
| Web fetch / Web search | ❌ Denegado |
| Lectura/Glob/Grep | ✅ Permitido |
| LSP | ✅ Permitido |
| Question | ✅ Permitido |

### Skills habilitadas
- `read` — Solo lectura
- `plan` — Planning
- `system-tools` — Referencia CLI

### Tools exclusivas
- `memos_*`, `sequential-thinking`, `pdf_*`
- `arxiv_*` (solo lectura de papers existentes)
- `web-search_*`, `context7_*`

### Casos de uso
- Explorar código sin riesgo de modificarlo
- Leer documentación y logs
- Auditoría de solo lectura

---

## `research` — Investigación Multidominio

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.15 |
| Acceso total | Sí |
| Prompt | *"You are a research specialist."* |

### Permisos

| Recurso | Acceso |
|---------|--------|
| Editar archivos | ✅ Permitido |
| Bash | ✅ Permitido |
| Task | ✅ Permitido |
| Web / Web search | ✅ Permitido |
| LSP | ✅ Permitido |
| Doom loop | ⚠️ Ask (pregunta antes de loops) |

### Skills habilitadas
- `deep-research` — 5 rondas de investigación iterativa
- `scientific-research` — Papers, compuestos, citas
- `scientific-computing` — Cálculos con Python científico
- `doc-scout` — Documentación técnica
- `fact-checker` — Verificación de fuentes
- `system-tools`

### Tools exclusivas
- Todo lo de `plan` +
- `pubchem_*` — Compuestos químicos
- `memory_*` — Memoria persistente

### Casos de uso
- Investigación científica (arXiv + PubChem)
- Búsqueda y validación de información web
- Documentación técnica de librerías
- Análisis de datos con Python científico

---

## `coding` — Developer General

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.15 |
| Acceso total | Sí |
| Prompt | *"You are a Developer specialist."* |

### Permisos

| Recurso | Acceso |
|---------|--------|
| Editar | ✅ |
| Bash | ✅ |
| Task | ✅ |
| Web / Web search | ✅ |
| LSP | ✅ |
| Doom loop | ⚠️ Ask |

### Skills habilitadas
- `coding` — Workflow completo (read → plan → implement → ruff → test → commit)
- `refactoring` — Refactorización segura
- `test-writer` — Tests unitarios, integración, E2E
- `tdd` — Test-driven development
- `commit-message` — Mensajes de commit convencionales
- `systematic-debugging` — Debug metódico
- `system-tools`

### Tools exclusivas
- `git_status`, `git_add`, `git_commit`, `git_diff`, `git_log`
- `git_push`, `git_pull`, `git_checkout`, `git_branch`
- `git_show`, `git_merge`, `git_fetch`, `git_reset`, `git_stash`
- `web-search_*`, `context7_*`, `pdf_*`

### Casos de uso
- Desarrollo de software en cualquier lenguaje
- Depuración de código
- Refactorización
- Code review y testing

---

## `coding-web` — Web Developer

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.15 |
| Acceso total | Sí |
| Prompt | *"You are a web development specialist."* |

### Permisos
Idéntico a `coding`.

### Skills habilitadas
- `coding`, `refactoring`, `test-writer`, `tdd`
- `commit-message`, `systematic-debugging`, `system-tools`

### Tools exclusivas (adicionales a coding)
- `browser_navigate`, `browser_click`, `browser_type`
- `browser_snapshot`, `browser_take_screenshot`
- `browser_evaluate`, `browser_wait_for`, `browser_tabs`
- `browser_fill_form`, `browser_hover`, `browser_select_option`
- `browser_close`, `browser_file_upload`, `browser_resize`
- `browser_run_code_unsafe`, `browser_network_request`
- `browser_handle_dialog`, `browser_press_key`

### Casos de uso
- Desarrollo frontend (React, Next.js, etc.)
- Automatización de navegador con Playwright
- Testing E2E
- Scraping web
- Desarrollo de APIs

---

## `code-quality` — Code Review & Quality

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.15 |
| Acceso total | Sí |
| Prompt | *"You are a code quality specialist."* |

### Permisos
Idéntico a `coding`.

### Skills habilitadas
- `code-reviewer` — Review de código (bugs, security, performance)
- `test-writer` — Tests
- `tdd` — TDD
- `refactoring` — Refactorización
- `system-tools`

### Tools exclusivas
- `sonarqube_search_sonar_issues` — Buscar issues de SonarQube
- `sonarqube_get_sonar_issue_context` — Contexto de issue
- `sonarqube_get_sonar_fix_plan` — Plan de fixes
- `sonarqube_get_quality_gate_status` — Estado de quality gate
- `sonarqube_get_rule_details` — Detalles de reglas
- `sonarqube_get_component_measures` — Métricas
- `sonarqube_search_sonar_projects` — Buscar proyectos
- `git_*` — Operaciones Git
- `pdf_*`

### Casos de uso
- Análisis estático de código con SonarQube
- Code reviews sistemáticos
- Identificación de deuda técnica
- Aseguramiento de calidad

---

## `build` — Build & Compilation

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.1 (mínima creatividad) |
| Acceso total | Sí |
| Prompt | *"You are a build specialist."* |

### Permisos
Idéntico a `coding`.

### Skills habilitadas
- `coding`, `refactoring`, `test-writer`, `tdd`
- `commit-message`, `systematic-debugging`, `system-tools`

### Tools exclusivas
- `sonarqube_*` — Análisis de código (como code-quality)
- `git_*` — Operaciones Git (como coding)
- `pdf_*`

### Casos de uso
- Compilación de proyectos
- Configuración de build systems (CMake, Make, webpack, etc.)
- Integración continua
- Automatización de builds

---

## `refactoring` — Refactorización Estructural

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.15 |
| Acceso total | Sí |
| Prompt | *"You are a refactoring specialist. Improve code structure while preserving behavior."* |

### Permisos
Idéntico a `coding`.

### Skills habilitadas
- `refactoring` — Refactorización con comby
- `system-tools`

### Tools exclusivas
- `git_*` — Operaciones Git
- `context7_*` — Documentación de librerías
- `pdf_*`

### Casos de uso
- Renombrar variables/funciones en masa
- Cambiar patrones de código estructuralmente
- Migrar APIs
- Aplicar transformaciones de código con comby

---

## `typescript-dev` — TypeScript/JavaScript Developer

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.15 |
| Acceso total | Sí |
| Prompt | *"You are a TypeScript/JavaScript developer. Load the coding skill."* |

### Permisos
Idéntico a `coding`.

### Skills habilitadas
- `coding`, `refactoring`, `test-writer`
- `system-tools`

### Tools exclusivas
- `git_*` — Operaciones Git
- `context7_*` — Documentación
- `web-search_*` — Búsqueda web
- `pdf_*`

### Casos de uso
- Desarrollo TypeScript/JavaScript
- Node.js, React, Next.js, NestJS
- npm/yarn/pnpm
- LSP TypeScript disponible

---

## `rust-dev` — Rust Developer

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.15 |
| Acceso total | Sí |
| Prompt | *"You are a Rust developer. Load the coding skill."* |

### Permisos
Idéntico a `coding`.

### Skills habilitadas
- `coding`, `refactoring`, `system-tools`

### Tools exclusivas
- `git_*` — Operaciones Git
- `context7_*` — Documentación
- `web-search_*` — Búsqueda web
- `pdf_*`

### Casos de uso
- Desarrollo Rust
- Cargo, crates, sistemas
- LSP rust-analyzer disponible

---

## `cpp-dev` — C/C++ Developer

| Propiedad | Valor |
|-----------|-------|
| Modo | `primary` |
| Temperatura | 0.15 |
| Acceso total | Sí |
| Prompt | *"You are a C/C++ developer. Load the coding skill."* |

### Permisos
Idéntico a `coding`.

### Skills habilitadas
- `coding`, `refactoring`, `system-tools`

### Tools exclusivas
- `git_*` — Operaciones Git
- `context7_*` — Documentación
- `web-search_*` — Búsqueda web
- `pdf_*`

### Casos de uso
- Desarrollo C/C++
- CMake, Make, sistemas embebidos
- LSP clangd disponible

---

## Referencia Rápida

### Clasificación por permisos

| Tipo | Agentes |
|------|---------|
| **Read-only total** | `read` |
| **Read-only (bash permitido)** | `plan` |
| **Full access (sin doom loop)** | `plan`, `read` |
| **Full access (doom loop: ask)** | `research`, `coding`, `coding-web`, `code-quality`, `build`, `refactoring`, `typescript-dev`, `rust-dev`, `cpp-dev` |

### Clasificación por especialidad

| Especialidad | Agentes |
|-------------|---------|
| **Planning/Documentación** | `plan`, `read` |
| **Investigación** | `research` |
| **Desarrollo general** | `coding`, `coding-web` |
| **Calidad/Review** | `code-quality` |
| **Build/Sistema** | `build`, `refactoring` |
| **Lenguajes específicos** | `typescript-dev`, `rust-dev`, `cpp-dev` |

### LSP por agente

| Agente | LSP disponibles |
|--------|-----------------|
| `coding`, `coding-web`, `typescript-dev` | TypeScript, Python, C/C++, Rust |
| `rust-dev` | Rust, Python, C/C++ |
| `cpp-dev` | C/C++, Python, TypeScript |
| `research`, `code-quality`, `build`, `refactoring` | Todos |

### Notas

- El agente default es `plan` (configurado en `default_agent`)
- El modelo default es `guzman-lopez/normal-gratis`
- Los agentes `typescript-dev`, `rust-dev`, `cpp-dev` no tienen `playwright` tools
- `read` es el único agente con `bash: deny` y `task: deny`
- `plan` es el único agente read-only con bash permitido
