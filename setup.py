#!/usr/bin/env python3
"""
opencode Environment Installer (Self-Contained)
================================================
Script completamente autonomo. Genera TODO el entorno opencode desde cero.
No necesita archivos externos — todo esta embebido.

Uso:
    python3 setup.py                           # Instala en directorio actual
    python3 setup.py --target /ruta/destino    # Instala en ruta especifica
    python3 setup.py --api-key TU_LLAVE        # Pasa la API key
    OPENCODE_API_KEY=TU_LLAVE python3 setup.py # O por variable de entorno
"""

import os
import sys
import platform
import subprocess
import argparse
import shutil
from pathlib import Path, PureWindowsPath, PurePosixPath

# Detectar OS una vez
IS_LINUX   = sys.platform == "linux"
IS_MAC     = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"
OS_NAME    = "linux" if IS_LINUX else ("mac" if IS_MAC else ("windows" if IS_WINDOWS else sys.platform))

# Soporte para terminales sin ANSI (Windows CMD, PowerShell antiguo)
def _enable_windows_ansi():
    """Habilita códigos ANSI en Windows 10+."""
    if not IS_WINDOWS:
        return
    try:
        import ctypes  # type: ignore
        kernel32 = ctypes.windll.kernel32  # type: ignore
        # Habilita ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x4)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass  # Fallar silenciosamente, no es crítico

_enable_windows_ansi()

# Helper: ejecutable de node_modules/.bin (Windows usa .cmd/.bat)
def npm_bin(name, base_dir):
    """Retorna la ruta al ejecutable de node_modules/.bin de forma cross-platform."""
    bin_dir = Path(base_dir) / "node_modules" / ".bin"
    if IS_WINDOWS:
        # npm en Windows crea archivos .cmd y .ps1 además de sin extensión
        for ext in [".cmd", ".bat", ".exe", ""]:
            candidate = bin_dir / (name + ext)
            if candidate.exists():
                return str(candidate)
    return str(bin_dir / name)

# Helper: comando para ejecutar en shell cross-platform
def shell_cmd(cmd):
    """Envuelve un comando para bash en Unix, cmd en Windows."""
    if IS_WINDOWS:
        return f'cmd /c "{cmd}"'
    return f'bash -c \'{cmd}\''

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  ARCHIVOS EMBEDIDOS — Todo el proyecto opencode esta aqui dentro           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ── package.json ──────────────────────────────────────────────────────────────
PACKAGE_JSON = r'''{
  "name": "opencode-mcp",
  "private": true,
  "type": "module",
  "dependencies": {
    "@opencode-ai/plugin": "1.16.2",
    "@playwright/mcp": "latest",
    "@sylphx/pdf-reader-mcp": "latest",
    "git-mcp-server": "^1.0.0",
    "mcp-sequential-thinking": "^0.6.7",
    "mcp-server-memory": "^1.0.3",
    "@cyanheads/pubchem-mcp-server": "latest",
    "typescript-language-server": "^5.3.0"
  },
  "devDependencies": {
    "@types/bun": "^1.3.14"
  }
}'''


# ── .env.example ───────────────────────────────────────────────────────────────
DOTENV_EXAMPLE = r'''# ============================================================
# Credenciales para OpenCode — Copiar a .env y rellenar
# ============================================================

# Proxy Cesar — API key para acceder a los modelos LLM
# (Compartida con el equipo)
PROXY_API_KEY=TU_API_KEY_AQUI

# SearXNG — Buscador privado (credenciales personales)
# URL del buscador
SEARXNG_URL=https://sear.guzman-lopez.com
# Usuario y contraseña (pedir al admin si no se tienen)
SEARXNG_USER=TU_USUARIO
SEARXNG_PASS=TU_CONTRASENA

# Memos MCP — Token de acceso al servidor de notas
MEMOS_MCP_TOKEN=TU_MEMOS_TOKEN_AQUI
'''

# ── tui.json ──────────────────────────────────────────────────────────────────
TUI_JSON = r'''{
  "$schema": "https://opencode.ai/tui.json",
  "theme": "system"
}'''

# ── .gitignore ────────────────────────────────────────────────────────────────
GITIGNORE = r'''# Dependencies
node_modules/
package-lock.json

# Ruff cache
.ruff_cache/

# OS / editor files
.DS_Store
Thumbs.db
.vscode/
*.bak

# API keys — NUNCA commitear
opencode.jsonc
.env
.env.*
*.key
*.pem
secrets.json

# Generated files
setup.log
__pycache__/
'''

# ── mcp/config.json ──────────────────────────────────────────────────────────
MCP_CONFIG = r'''{
  "mcp_servers": {},
  "scripts_dir": "SCRIPTS_DIR_PLACEHOLDER"
}'''

# ── PLUGINS (.ts) ────────────────────────────────────────────────────────────
PLUGINS = {}

PLUGINS["bat.ts"] = r'''import { type Plugin, tool } from "@opencode-ai/plugin"

export const BatPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      "bat": tool({
        description: "Display file contents with syntax highlighting, line numbers, and git modification markers. Better than cat.",
        args: {
          path: tool.schema.string().describe("File path to display"),
          language: tool.schema.string().optional().describe("Language for syntax highlighting"),
          lines: tool.schema.number().optional().describe("Show last N lines only"),
        },
        async execute(args, context) {
          const dir = context.worktree || context.directory || "."
          const filePath = args.path.startsWith("/") ? args.path : `${dir}/${args.path}`
          const langArg = args.language ? ["-l", args.language] : []
          const cmd = ["bat", "--paging=never", ...langArg, filePath]
          
          try {
            let result
            if (args.lines) {
              const full = await Bun.$`${cmd}`.text()
              result = full.split("\n").slice(-args.lines).join("\n")
            } else {
              result = await Bun.$`${cmd}`.text()
            }
            return result || "(empty file)"
          } catch (e) {
            const err = String(e)
            if (err.includes("not found")) {
              return "bat not installed. Install: sudo pacman -S bat / brew install bat / apt install bat"
            }
            return `Error: ${err.slice(0, 200)}`
          }
        },
      }),
    },
  }
}
'''

PLUGINS["comby.ts"] = r'''import { type Plugin, tool } from "@opencode-ai/plugin"

export const CombyPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      "comby-search": tool({
        description: "Structural code search using comby. Like grep but understands code syntax (functions, loops, etc). Supports: py, js, ts, go, rs, java, c, cpp, ruby, scala, swift, kotlin, lua, ocaml, Haskell, Elm, Nix, proto, LaTeX, Makefile, Dockerfile, shell.",
        args: {
          template: tool.schema.string().describe("Pattern with holes (e.g. 'func :[fn](:[args]) { :[body] }' or 'for (:[_] in :[_]) { :[_] }')"),
          path: tool.schema.string().default(".").describe("File, directory, or glob pattern"),
          language: tool.schema.string().optional().describe("Language: py, js, go, rs, java, c, etc."),
        },
        async execute(args, context) {
          const dir = context.worktree || context.directory || "."
          const lang = args.language ? ["-lang", args.language] : []
          try {
            const result = await Bun.$`cd ${dir} && comby -matcher '${args.template}' ${lang.join(' ')} -json ${args.path}`.text()
            const matches = JSON.parse(result)
            if (matches.length === 0) {
              return "No matches found"
            }
            return matches.map((m: any) => JSON.stringify({
              matched: m.match,
              range_start: m.range?.start?.toString() || "",
              range_end: m.range?.end?.toString() || ""
            })).join("\n")
          } catch (e: any) {
            return `Error: ${e.message}`
          }
        },
      }),
      "comby-replace": tool({
        description: "Structural code replacement using comby. Rewrites code patterns safely. Dry-run by default.",
        args: {
          template: tool.schema.string().describe("Pattern to match (e.g. 'func :[fn](:[args]) { :[body] }')"),
          replacement: tool.schema.string().describe("Replacement with captures (e.g. 'def :[fn](:[args]):\n    :[body]')"),
          path: tool.schema.string().default(".").describe("File, directory, or glob"),
          language: tool.schema.string().optional().describe("Language hint"),
          apply: tool.schema.boolean().optional().default(false).describe("Set true to write changes (default: preview only)"),
        },
        async execute(args, context) {
          const dir = context.worktree || context.directory || "."
          const lang = args.language ? ["-lang", args.language] : []
          const writeFlag = args.apply ? ["--in-place"] : []
          try {
            let result
            if (args.apply) {
              result = await Bun.$`cd ${dir} && comby -matcher '${args.template}' -rewrite '${args.replacement}' ${lang.join(' ')} ${writeFlag.join(' ')} ${args.path}`.text()
              return result || "Changes applied successfully"
            } else {
              result = await Bun.$`cd ${dir} && comby -matcher '${args.template}' -rewrite '${args.replacement}' ${lang.join(' ')} -json ${args.path}`.text()
              const changes = JSON.parse(result)
              if (changes.length === 0) {
                return "No replacements made"
              }
              return JSON.stringify({
                rewritten_source: `Would apply: comby -matcher '${args.template}' -rewrite '${args.replacement}' ${lang.join(' ')} ${args.path}`
              })
            }
          } catch (e: any) {
            return `Error: ${e.message}`
          }
        },
      }),
    },
  }
}
'''

PLUGINS["plotext.ts"] = r'''import { type Plugin, tool } from "@opencode-ai/plugin"

export const PlotextPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      "chart": tool({
        description: "Generate a terminal-based chart (bar, line, scatter, pie) from data using plotext Python library.",
        args: {
          type: tool.schema.enum(["bar", "line", "scatter", "pie"]).describe("Chart type"),
          data: tool.schema.string().describe("Data as JSON array. For bar/line: [{label, value}] or [value]. For pie: [{label, value}]"),
          title: tool.schema.string().optional().describe("Chart title"),
          xlabel: tool.schema.string().optional().describe("X-axis label"),
          ylabel: tool.schema.string().optional().describe("Y-axis label"),
          width: tool.schema.number().optional().default(80).describe("Width in characters"),
        },
        async execute(args, context) {
          const dir = context.worktree || context.directory || "."
          const script = `
import json, sys
try:
    import plotext as plt
except ImportError:
    print("plotext not installed. Run: pip install plotext")
    sys.exit(0)
data = json.loads(\\'\\'\\'${args.data}\\'\\'\\')
if "${args.title}": plt.title("${args.title}")
if "${args.xlabel}": plt.xlabel("${args.xlabel}")
if "${args.ylabel}": plt.ylabel("${args.ylabel}")
plt.plot_size(${args.width || 80}, 20)
if "${args.type}" == "bar":
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        plt.bar([d.get("label", str(i)) for i,d in enumerate(data)], [d.get("value", 0) for d in data])
    else:
        plt.bar(range(len(data)), data)
elif "${args.type}" == "line":
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        plt.plot([d.get("label", str(i)) for i,d in enumerate(data)], [d.get("value", 0) for d in data])
    else:
        plt.plot(data)
elif "${args.type}" == "scatter":
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        plt.scatter([d.get("x", i) for i,d in enumerate(data)], [d.get("y", 0) for d in data])
    else:
        plt.scatter(range(len(data)), data)
elif "${args.type}" == "pie":
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        plt.pie([d.get("label", str(i)) for i,d in enumerate(data)], [d.get("value", 0) for d in data])
    else:
        plt.pie([str(i) for i in range(len(data))], data)
plt.show()
`
          const result = await Bun.$`cd ${dir} && python3 -c ${script}`.text().catch(e => `Error: ${e.message}`)
          return result || "Chart generated"
        },
      }),
    },
  }
}
'''

PLUGINS["ruff.ts"] = r'''import { type Plugin, tool } from "@opencode-ai/plugin"

export const RuffPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      ruff: tool({
        description: "Lint, format, or fix Python files with Ruff. Auto-detects best runner: poetry, uvx, or direct ruff.",
        args: {
          action: tool.schema.enum(["check", "format", "fix", "check-ci"]).describe("Action to perform"),
          path: tool.schema.string().default(".").describe("File, directory, or glob pattern to process"),
        },
        async execute(args, context) {
          const dir = context.worktree || context.directory || "."
          const p = args.path
          const ruffCmd = await detectRuff(dir)
          if (!ruffCmd) return "Ruff not found. Install: pip install ruff"
          let cmdArgs
          switch (args.action) {
            case "format": cmdArgs = [ruffCmd, "format", p]; break
            case "fix": cmdArgs = [ruffCmd, "check", "--fix", p, "&&", ruffCmd, "format", p]; break
            case "check-ci": cmdArgs = [ruffCmd, "check", "--output-format=concise", p]; break
            default: cmdArgs = [ruffCmd, "check", p]
          }
          const result = await Bun.$`cd ${dir} && ${cmdArgs}`.text().catch((e) => e.message || String(e))
          return result.trim() || "No issues found"
        },
      }),
    },
  }
}

async function detectRuff(dir) {
  for (const runner of [`poetry run ruff`, `uvx ruff`, `ruff`]) {
    try {
      const parts = runner.split(" ")
      const out = await Bun.$`cd ${dir} && ${parts} --version 2>/dev/null`.text()
      if (out.trim()) return runner
    } catch { /* try next */ }
  }
  return null
}
'''

PLUGINS["verify-deps.ts"] = r'''import { type Plugin, tool } from "@opencode-ai/plugin"

const MCP_MAP = {
  "context7": "@upstash/context7-mcp",
  "web-search": "searxng-mcp (Python)",
  "arxiv": "arxiv-mcp-server",
  "pdf": "@sylphx/pdf-reader-mcp",
  "git": "git-mcp-server",
  "pubchem": "@cyanheads/pubchem-mcp-server",
  "playwright": "@playwright/mcp",
  "sequential-thinking": "mcp-sequential-thinking",
  "memory": "mcp-server-memory",
}

export const VerifyDepsPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      "verify-deps": tool({
        description: "Verify all system dependencies for opencode tools. Reports what's missing and how to install it.",
        args: {
          fix: tool.schema.boolean().optional().default(false).describe("Attempt to install missing dependencies"),
          category: tool.schema.enum(["all", "mcp", "system", "python"]).optional().default("all").describe("Category"),
          cleanup: tool.schema.boolean().optional().default(false).describe("Generate JSON to disable non-functional MCPs"),
        },
        async execute(args, context) {
          const check = async (name, cmd, required, hint) => {
            const found = await Bun.$`bash -c '${cmd}' 2>/dev/null`.then(r => r.exitCode === 0).catch(() => false)
            return { name, required, found, hint }
          }
          const results = []
          let output = ""
          if (args.category === "all" || args.category === "system") {
            results.push(await check("Node.js", "node --version", true, "Install from https://nodejs.org"))
            results.push(await check("npm/npx", "npx --version", true, "Comes with Node.js"))
            results.push(await check("Python 3", "python3 --version", true, "Install from https://python.org"))
            results.push(await check("uv/uvx", "uvx --version", false, "curl -LsSf https://astral.sh/uv/install.sh | sh"))
            results.push(await check("Git", "git --version", true, "Install from https://git-scm.com"))
            results.push(await check("pdftoppm", "pdftoppm --version 2>&1 | head -1", false, "pacman -S poppler | brew install poppler | choco install poppler"))
            results.push(await check("comby", "comby --version 2>&1", false, "yay -S comby-bin (Arch) / brew install comby (macOS) / https://github.com/comby-tools/comby/releases"))
          }
          if (args.category === "all" || args.category === "mcp") {
            for (const [name, pkg] of Object.entries(MCP_MAP)) {
              if (name === "web-search") {
                // searxng-mcp is a local Python script, not an npm package
                const home = process.env.HOME || process.env.USERPROFILE || ""
                results.push(await check("mcp: web-search", `test -f ${home}/.config/opencode/bin/searxng-mcp.py && echo "ok"`, false, "Run setup.py or copy bin/searxng-mcp.py manually"))
              } else {
                results.push(await check(`mcp: ${name}`, `npx -y ${pkg} --version 2>&1`, false, `npx -y ${pkg}`))
              }
            }
          }
          const missing = results.filter(r => !r.found)
          const ok = results.filter(r => r.found)
          output += `## Summary\n✅ ${ok.length} found | ❌ ${missing.length} missing\n\n`
          if (ok.length > 0) output += ok.map(r => `✅ ${r.name}`).join("\n") + "\n\n"
          if (missing.length > 0) output += missing.map(r => `❌ ${r.required ? 'REQUIRED' : 'optional'} ${r.name}\n   Install: ${r.hint}`).join("\n") + "\n"
          if (args.cleanup && missing.length > 0) {
            const failed = missing.filter(r => r.name.startsWith("mcp:")).map(r => r.name.replace("mcp: ", ""))
            if (failed.length > 0) output += `\n## Disable these MCPs in opencode.json:\n` + failed.map(n => `"${n}": { "enabled": false }`).join("\n")
          }
          return output
        },
      }),
    },
  }
}
'''

PLUGINS["verify-opencode.ts"] = r'''import { type Plugin, tool } from "@opencode-ai/plugin"

export const VerifyOpencodePlugin: Plugin = async (ctx) => {
  return {
    tool: {
      "verify-opencode": tool({
        description: "Verify opencode configuration is valid. Checks agents, MCPs, LSP, and config syntax. Admin-only tool.",
        args: { detailed: tool.schema.boolean().optional().default(false).describe("Show detailed output") },
        async execute(args, context) {
          let output = "# OpenCode Verification Report\n\n"
          const home = process.env.HOME || process.env.USERPROFILE || ""
          const configPath = home ? `${home}/.config/opencode/opencode.jsonc` : "~/.config/opencode/opencode.jsonc"

          const check = async (name, cmd, timeoutMs = 5000) => {
            try {
              const result = await Bun.$`bash -c '${cmd}'`.timeout(timeoutMs).text()
              return { name, status: "✅", detail: result.trim().slice(0, 80) }
            } catch {
              return { name, status: "❌", detail: "Not found or failed" }
            }
          }
          const results = []
          results.push(await check("Config JSON", `python3 -m json.tool ${configPath} 2>/dev/null && echo VALID || echo INVALID`))
          try {
            const agents = await Bun.$`opencode agent list 2>&1`.timeout(10000).text()
            const count = agents.split("\n").filter(l => l.includes("primary")).length
            results.push({ name: "Agents", status: count > 10 ? "✅" : "⚠️", detail: `${count} agents` })
          } catch { results.push({ name: "Agents", status: "❌", detail: "Cannot list agents" }) }
          try {
            const mcps = await Bun.$`opencode mcp ls 2>&1`.timeout(10000).text()
            const conn = (mcps.match(/connected/g) || []).length
            const fail = (mcps.match(/failed/g) || []).length
            results.push({ name: "MCPs", status: fail === 0 ? "✅" : "⚠️", detail: `${conn} connected, ${fail} failed` })
          } catch { results.push({ name: "MCPs", status: "❌", detail: "Cannot list MCPs" }) }
          results.push(await check("Node.js", "node --version"))
          results.push(await check("uvx", "uvx --version 2>&1"))
          results.push(await check("pylsp", "pylsp --version 2>&1"))
          results.push(await check("pdftoppm", "pdftoppm --version 2>&1 | head -1"))

          for (const r of results) {
            const show = args.detailed || r.status === "❌"
            if (show) output += `${r.status} ${r.name}: ${r.detail}\n`
          }
          const failCount = results.filter(r => r.status === "❌").length
          output += `\n---\n${failCount === 0 ? "✅ ALL SYSTEMS OPERATIONAL" : `❌ ${failCount} issue(s)`}\n`
          return output
        },
      }),
    },
  }
}
'''

PLUGINS["research-save.ts"] = r'''import { type Plugin, tool } from "@opencode-ai/plugin"

export const ResearchSavePlugin: Plugin = async (ctx) => {
  return {
    tool: {
      "research-save": tool({
        description: "Save final research report. MUST call at end of research.",
        args: {
          topic: tool.schema.string().describe("Research topic (folder name)"),
          title: tool.schema.string().describe("Report title"),
          rounds: tool.schema.number().describe("Rounds completed"),
          executive_summary: tool.schema.string().describe("2-3 paragraph summary"),
          key_findings: tool.schema.string().describe("Detailed findings"),
          sources: tool.schema.string().describe("Sources (URLs, DOIs)"),
          conclusions: tool.schema.string().describe("Conclusions"),
        },
        async execute(args, context) {
          const dir = context.worktree || context.directory || "."
          const slug = args.topic.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 50)
          const folder = `${dir}/research/${slug}`
          const date = new Date().toISOString().split("T")[0]
          const filename = `${date}-final-report.md`
          
          const report = `# ${args.title}\n\n**Date:** ${date}\n**Rounds:** ${args.rounds}\n\n## Executive Summary\n\n${args.executive_summary}\n\n## Key Findings\n\n${args.key_findings}\n\n## Sources\n\n${args.sources}\n\n## Conclusions\n\n${args.conclusions}\n\n---\n*Full notes: research/${slug}/index.md*`

          await Bun.$`mkdir -p ${folder}`.text()
          await Bun.write(`${folder}/${filename}`, report)

          return `✅ research/${slug}/${filename}\n\n**Executive Summary:**\n${args.executive_summary.slice(0, 500)}`
        },
      }),
    },
  }
}
'''

PLUGINS["save-findings.ts"] = r'''import { type Plugin, tool } from "@opencode-ai/plugin"

export const SaveFindingsPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      "save-findings": tool({
        description: "Save findings to research/<topic>/ folder. Auto-updates index.md.",
        args: {
          topic: tool.schema.string().describe("Research topic (folder name)"),
          content: tool.schema.string().describe("Content in markdown"),
          filename: tool.schema.string().describe("Filename (e.g. round-1, subtask-arxiv)"),
          summary: tool.schema.string().optional().describe("One-line summary for index"),
        },
        async execute(args, context) {
          const dir = context.worktree || context.directory || "."
          const slug = args.topic.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 50)
          const folder = `${dir}/research/${slug}`
          const fname = args.filename.replace(/[^a-z0-9_-]/g, "") + ".md"
          const date = new Date().toISOString().split("T")[0]
          const content = `---\nfilename: ${fname}\ndate: ${date}\n---\n\n${args.content}`

          await Bun.$`mkdir -p ${folder}`.text()
          await Bun.write(`${folder}/${fname}`, content)

          const summary = args.summary || args.content.slice(0, 100).replace(/\n/g, " ")
          const indexLine = `- [${fname}](${fname}) — ${summary}\n`
          const indexPath = `${folder}/index.md`
          let indexContent = ""
          try { indexContent = await Bun.$`cat ${indexPath} 2>/dev/null || true`.text() } catch {}
          if (!indexContent) indexContent = `# Research: ${args.topic}\n\nStarted: ${date}\n\n## Files\n\n`
          if (!indexContent.includes(fname)) indexContent += indexLine
          await Bun.write(indexPath, indexContent)

          return `✅ research/${slug}/${fname}\n📋 Index: research/${slug}/index.md`
        },
      }),
      "load-findings": tool({
        description: "Load research files. Use list_all for index, or specify topic+filename.",
        args: {
          topic: tool.schema.string().optional().describe("Research topic folder"),
          filename: tool.schema.string().optional().describe("Filename (without .md)"),
          list_all: tool.schema.boolean().optional().default(false).describe("List all research folders"),
        },
        async execute(args, context) {
          const dir = context.worktree || context.directory || "."
          if (args.list_all) {
            const folders = await Bun.$`ls -d ${dir}/research/*/ 2>/dev/null || true`.text()
            if (!folders.trim()) return "No research folders found."
            let out = "## Research folders\n\n"
            for (const f of folders.trim().split("\n")) {
              const name = f.split("/").slice(-2)[0]
              const idx = await Bun.$`cat ${f}index.md 2>/dev/null | head -3 || true`.text()
              out += `### ${name}\n${idx}\n\n`
            }
            return out
          }
          if (args.topic) {
            const slug = args.topic.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 50)
            if (args.filename) {
              return await Bun.$`cat ${dir}/research/${slug}/${args.filename}.md 2>/dev/null || echo "Not found"`.text()
            }
            return await Bun.$`cat ${dir}/research/${slug}/index.md 2>/dev/null || echo "No index"`.text()
          }
          return "Specify topic or use list_all=true"
        },
      }),
    },
  }
}
'''

# ── SKILLS ────────────────────────────────────────────────────────────────────
SKILLS = {}

SKILLS["coding/SKILL.md"] = r'''---
name: coding
description: General-purpose coding instructions for all coding agents.
---
Available: ruff, git, pdf, web-search, arxiv, playwright, sequential-thinking, memory, comby-search, comby-replace.

Workflow: read code → plan → implement → **MUST ruff check** → test → commit.

Rules:
- **ALWAYS run ruff check on modified Python files.** This is mandatory, not optional.
- If ruff finds errors, fix them before proceeding.
- Only skip ruff check if the file is not Python.
- Use git for version control.
- Prefer minimal focused changes.
- Never leave dead code.
'''

SKILLS["code-reviewer/SKILL.md"] = r'''---
name: code-reviewer
description: Reviews code for best practices, potential issues, and quality. Read-only.
---
Do NOT modify files. You are read-only.

For large reviews, delegate individual file reviews with task:
task({ agent: read, task: 'review file X for bugs' })

Protocol:
1. Read the code to review.
2. Analyze for: bugs, security issues, performance, code style, test coverage.
3. Provide feedback with specific line references.
4. If reviewing many files, use task to delegate per-file.

Rules: be specific, reference line numbers, prioritize security and correctness.
'''

SKILLS["deep-research/SKILL.md"] = r'''---
name: deep-research
description: Deep iterative research: ALL tools, multi-round research loop, saves comprehensive report.
---
You MUST complete ALL 5 rounds. Call research-save in round 5. FAILURE TO SAVE = TASK FAILED.

ROUND 1 — SCOUT:
1. Call sequentialthinking to break question into 3-5 sub-topics.
2. Search each sub-topic with web-search_full-web-search (multi-engine: Bing/DuckDuckGo).
3. Use web-search_get-single-web-page-content to read detailed results.
4. List what you found and what gaps remain.
5. Call save-findings with filename="round-1" to persist findings.
6. DO NOT proceed without listing gaps.

ROUND 2 — DIVE:
1. Load findings from round 1 with load-findings.
2. Pick 3-5 most promising results.
3. Use web-search_get-single-web-page-content for deep page extraction.
4. Use playwright_browser_navigate if page needs JavaScript rendering.
5. Use read_pdf if there are PDF papers.
6. Identify what's still missing.
7. Call save-findings with filename="round-2".

ROUND 3 — ITERATE:
1. Load previous findings.
2. Generate 2-3 new search queries from gaps.
3. Search again with web-search_full-web-search.
4. For scientific papers: arxiv_search_papers or pubchem_search_compounds.
5. Store key facts with memory_add_observations.
6. Call save-findings with filename="round-3".
7. Assess convergence. If no new info → proceed to verify.

ROUND 4 — VERIFY:
1. Load all previous findings.
2. Each claim needs 2+ independent sources.
3. Check dates — prefer 2025-2026.
4. Flag contradictions explicitly.
5. Call save-findings with filename="round-4".

ROUND 5 — FINALIZE:
1. Load all previous findings.
2. Compile into structured report.
3. YOU MUST CALL research-save.
4. Report saved to ./research/<topic>/<date>-report.md.
5. CONFIRM save appears. If not, retry.

RULES:
- SAVE EVERYTHING. Never trust context memory.
- Never finish without research-save.
- Use save-findings for each round, each finding.
- Load only what you need with load-findings.
- Always include summary for the index.
- If task fails, retry once. If still fails, document and continue.
- Use sequentialthinking before each round.
'''

SKILLS["doc-scout/SKILL.md"] = r'''---
name: doc-scout
description: Finds technical documentation, API references, library docs, and code examples.
---
Available: web-search (multi-engine search + page extraction), playwright, sequential-thinking.

Focus: library/framework API docs, config guides, code examples, release notes, migration guides.

Process:
1. Identify exact library+version
2. Search official docs first using web-search_full-web-search
3. Use web-search_get-single-web-page-content to extract documentation content
4. Extract function signatures/params/examples
5. Note version.

Rules: prefer official docs over third-party, include version numbers, never invent APIs.
'''

SKILLS["fact-checker/SKILL.md"] = r'''---
name: fact-checker
description: Verifies claims, finds primary sources, checks accuracy of information.
---
Available: web-search (multi-engine search + page extraction), playwright, sequential-thinking.

Protocol:
1. Identify the claim
2. Search in 2+ independent sources using web-search_full-web-search
3. Use web-search_get-single-web-page-content to read primary sources
4. Prioritize: primary sources > official docs > reputable news > expert analysis
5. Check dates, evaluate authority
6. Determine: confirmed / likely true / unverifiable / likely false / debunked

Rules: be conservative, always cite sources for both sides, distinguish errors from outdated info from opinion.
'''

SKILLS["plan/SKILL.md"] = r'''---
name: plan
description: Planning and analysis. Read-only to prevent accidental changes.
---
You are a senior tech lead focused on planning and analysis.

Rules:
- Read and analyze code thoroughly before suggesting changes.
- Break down requirements into small, actionable steps.
- Identify risks, edge cases, and dependencies.
- Never modify files or run commands.
- If execution is needed, explain why and suggest using @coding-python or @coding-web.
- Never invent file paths, URLs, or API endpoints.
'''

SKILLS["scientific-research/SKILL.md"] = r'''---
name: scientific-research
description: Scientific research: papers, compounds, citations, resources. Uses arXiv, PubChem, Crossref, web-search. Saves report to file.
---
# Scientific Research

Divide research into independent sub-tasks. Delegate each with task to save tokens.

## Protocol

1. **SCOPING** — Define domain, key terms, research questions
2. **LITERATURE SEARCH** — arXiv for papers, PubChem for compounds, Crossref for citations
3. **WEB CONTEXT** — web-search_full-web-search for supplementary info and context
4. **DEEP DETAILS** — Extract DOIs, CIDs, key findings, methodologies
5. **VERIFY** — Cross-check across 2+ independent sources
6. **SAVE REPORT** — Call research-save to persist final report to ./research/

## Task Delegation

For large research, delegate sub-tasks:
- Literature: `task({ agent: research-web, task: 'search arXiv for X' })`
- Compounds: `task({ agent: research-web, task: 'search PubChem for Y' })`
- Web context: `task({ agent: research-web, task: 'find supplementary info on Z' })`

Each sub-task MUST call save-findings to persist results.

## Tools Available

- arxiv: papers and preprints
- pubchem: chemical compounds and data
- web-search: supplementary information
- pdf: read research papers
- playwright: access web resources
- memory: store key findings

## Rules

- This is RESEARCH not code — do NOT use git/grep/code tools
- Include DOIs and CIDs wherever possible
- Verify across 2+ independent sources
- Never invent data or citations
- Always save final report with research-save
'''

SKILLS["read/SKILL.md"] = r'''---
name: read
description: Pure read-only mode. Cannot edit, run commands, or modify anything.
---
Do not modify files, run commands, or make any changes. Never invent facts.
'''

SKILLS["refactoring/SKILL.md"] = r'''---
name: refactoring
description: Refactors code improving structure and readability without changing behavior. Uses comby.
---
You are a refactoring specialist.

Available: git, comby-search, comby-replace, sequential-thinking.

Process:
1. Understand the current code structure.
2. Plan the refactoring: what to change and why.
3. Use comby for structural search and replace.
4. Run tests after each change.
5. Commit incrementally.

Rules: preserve behavior, one refactor per commit, never mix refactor with feature changes.
'''

SKILLS["scientific-computing/SKILL.md"] = r'''---
name: scientific-computing
description: Scientific computing: calculations, simulations, data analysis. Uses sympy, scipy, pandas via Python.
---
Available: bash (python with sympy/scipy/numpy/pandas/matplotlib/pint/numexpr), sequential-thinking, memory, ruff.

Workflow:
1. Understand problem
2. Plan
3. Write Python script
4. Run
5. Present results with proper units and significant figures.

Rules: never invent formulas or constants, include units, cross-check results.
'''

SKILLS["scientific-research/SKILL.md"] = r'''---
name: scientific-research
description: Academic research: papers, chemical compounds, citations. Uses arXiv, PubChem, Crossref. Saves report to file.
---
Divide research into independent sub-tasks. Delegate each with task to save tokens.

1. Plan: break into sub-topics (literature, compounds, citations).
2. For literature: task({ agent: research-web, task: 'search arXiv for X' }).
3. For compounds: task({ agent: research-web, task: 'search PubChem for Y' }).
4. Each sub-task MUST call save-findings to persist results.
5. Collect: load-findings to read all results.
6. Compile and call research-save to save final report.

Rules: include DOIs and CIDs, verify across 2+ sources, never invent data.
'''

SKILLS["system-tools/SKILL.md"] = r'''---
name: system-tools
description: Reference of CLI tools useful for AI agents, what they do, and how to install them.
---
Reference of CLI tools useful for AI agents.

## Busqueda
- rg (ripgrep): buscar texto en archivos
- fd: buscar archivos por nombre
- bat: ver archivos con syntax highlighting
- jq: procesar JSON
- comby: busqueda estructural de codigo

## Visualizacion
- gnuplot: graficas PNG/SVG
- ttyplot: graficas en tiempo real
- plotext: graficas en terminal (Python)
- rich: tablas/arboles con colores (Python)

## Instalacion
Arch:  sudo pacman -S <tool>
macOS: brew install <tool>
Debian: sudo apt install <tool>
Python: pip install <tool>

## Plugins relacionados
- bat: muestra archivos con syntax highlighting
- chart: genera graficas en terminal con plotext
'''

SKILLS["test-writer/SKILL.md"] = r'''---
name: test-writer
description: Writes unit tests, integration tests, and E2E tests. Covers edge cases and mocks.
---
You are a test specialist.

Available: git, playwright, web-search, sequential-thinking.

Process:
1. Understand the function/module to test.
2. Write tests covering: happy path, edge cases, error states, boundary conditions.
3. Use mocks for external dependencies.
4. Run tests and fix failures.

Rules: each test tests one thing, use descriptive test names, follow project test patterns.
'''

SKILLS["commit-message/SKILL.md"] = r'''---
name: commit-message
description: Generates clean, conventional commit messages from staged git diffs. Use when writing git commits.
---
# Commit Message Generator

## Instructions

1. Run `git diff --staged` to see all changes
2. Analyze the changes and generate a commit message

## Commit Format

```
<type>(<scope>): <short summary>

<detailed description>

<breaking changes if any>
```

## Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring without behavior change
- `docs`: Documentation only
- `test`: Adding or updating tests
- `chore`: Build, CI, dependencies
- `perf`: Performance improvement
- `style`: Formatting, no logic change

## Rules

- Use present tense ("add feature" not "added feature")
- Explain what and why, not how
- Keep subject line under 72 characters
- Reference issue numbers at the end (e.g., #123)
- Separate subject from body with blank line

## Examples

```
feat(auth): add JWT token refresh mechanism

Implement automatic token refresh when access token expires.
Uses refresh token stored in httpOnly cookie.

Closes #456
```

```
fix(api): handle null response from external service

The weather API sometimes returns null for invalid locations.
Added null check and fallback to default values.

Fixes #789
```
'''

SKILLS["systematic-debugging/SKILL.md"] = r'''---
name: systematic-debugging
description: Methodical problem-solving for bugs and errors. Use when debugging issues or investigating failures.
---
# Systematic Debugging

## Process

1. **Reproduce** — Create minimal steps to trigger the bug
2. **Isolate** — Narrow down to the smallest possible scope
3. **Hypothesize** — Form 2-3 possible causes
4. **Test** — Verify each hypothesis with evidence
5. **Fix** — Apply the minimal fix that addresses root cause
6. **Verify** — Confirm the fix works and doesn't break other things

## Rules

- Never guess. Always verify with evidence.
- Start from what you know, not what you think.
- Change one thing at a time.
- Document each step and finding.
- Check the simplest explanation first.

## Common Debugging Patterns

### Code not executing
- Check if the code path is actually reached (add log/print)
- Verify imports and module loading
- Check for syntax errors that prevent loading

### Wrong output
- Trace data flow from input to output
- Check intermediate values at each step
- Verify assumptions about data types and formats

### Performance issues
- Profile before optimizing
- Check for N+1 queries, unnecessary loops, missing indexes
- Measure actual vs expected complexity

### Intermittent failures
- Check for race conditions, shared state, timing issues
- Look at logs for patterns (time of day, load, etc.)
- Check external dependencies (APIs, databases, networks)

## Output Format

When debugging, always output:
1. What you observed
2. What you expected
3. Steps to reproduce
4. Hypotheses tested
5. Root cause found
6. Fix applied
7. Verification results
'''

SKILLS["tdd/SKILL.md"] = r'''---
name: tdd
description: Test-driven development workflow. Write tests first, then implement. Use when building new features or fixing bugs.
---
# Test-Driven Development (TDD)

## The Red-Green-Refactor Cycle

```
1. RED   — Write a failing test that defines desired behavior
2. GREEN — Write minimal code to make the test pass
3. REFACTOR — Clean up code while keeping tests green
```

## Process

### Step 1: Understand Requirements
- What should the code do?
- What are the inputs and outputs?
- What are the edge cases?

### Step 2: Write Failing Tests (RED)
- Start with the simplest test case
- Test one behavior per test
- Use descriptive test names
- Run tests to confirm they fail

### Step 3: Implement Minimal Code (GREEN)
- Write just enough code to pass
- Don't optimize yet
- Don't handle edge cases yet
- Run tests to confirm they pass

### Step 4: Refactor (REFACTOR)
- Improve code structure
- Remove duplication
- Add edge case handling
- Run tests to confirm nothing broke

## Rules

- Never write production code without a failing test first
- One test at a time
- Commit after each green-refactor cycle
- Tests are documentation — make them readable

## Test Structure

```python
def test_<what>():
    # Arrange — set up test data
    # Act — call the function
    # Assert — verify the result
```

## What to Test

- Happy path (expected behavior)
- Edge cases (boundaries, empty input, null)
- Error cases (invalid input, exceptions)
- Integration points (APIs, databases)

## Anti-Patterns to Avoid

- Testing implementation details (test behavior, not internals)
- Writing tests after code (defeats the purpose)
- Skipping the refactor step (technical debt accumulates)
- Testing too much at once (keep tests small and focused)

## When to Apply TDD

- New features with clear requirements
- Bug fixes (write test that reproduces bug first)
- Refactoring (tests ensure behavior doesn't change)
- Complex algorithms
- API endpoints

## Output

For each feature, produce:
1. Test file with failing tests
2. Implementation file
3. All tests passing
4. Refactored code
'''

# ── opencode.jsonc (plantilla) ───────────────────────────────────────────────
# {BASE_DIR} se reemplaza con la ruta real al instalar
# {API_KEY} se reemplaza con la key del usuario

OPENCODE_JSONC = r'''{
  "$schema": "https://opencode.ai/config.json",

  "default_agent": "plan",
  "autoupdate": "notify",
  "plugin": [],

  "provider": {
    "guzman-lopez": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "guzman-lopez",
      "modalities": {
        "input": ["text", "image", "pdf"],
        "output": ["text"]
      },
      "options": {
        "baseURL": "https://llm.guzman-lopez.com/v1",
        "apiKey": "{API_KEY}"
      },
      "models": {
        "pensamiento-profundo-caro": {
          "name": "Pensamiento Profundo",
          "capabilities": {
            "tools": true, "vision": true, "streaming": true,
            "function_calling": true, "parallel_tool_calls": true
          },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "tareas-avanzadas": {
          "name": "Tareas Avanzadas",
          "capabilities": {
            "tools": true, "vision": true, "streaming": true,
            "function_calling": true, "parallel_tool_calls": true
          },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "normal": {
          "name": "Normal",
          "capabilities": {
            "tools": true, "vision": true, "streaming": true,
            "function_calling": true, "parallel_tool_calls": true
          },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "vision": {
          "name": "Visión",
          "capabilities": {
            "tools": true, "vision": true, "streaming": true,
            "function_calling": true, "parallel_tool_calls": false
          },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "normal-gratis": {
          "name": "Normal Gratis",
          "capabilities": {
            "tools": true, "vision": true, "streaming": true,
            "function_calling": true, "parallel_tool_calls": true
          },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "flash": {
          "name": "Flash",
          "capabilities": {
            "tools": true, "vision": true, "streaming": true,
            "function_calling": true, "parallel_tool_calls": false
          },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "compactador": {
          "name": "Compactador",
          "capabilities": {
            "tools": false, "vision": true, "streaming": true,
            "function_calling": false, "parallel_tool_calls": false
          },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        }
      }
    }
  },

  "agent": {
    "plan": {
      "mode": "primary",
      "description": "Planning, analysis, and documentation research. Read-only.",
      "temperature": 0.1,
      "prompt": "You are a senior tech lead for planning and documentation research.",
      "permission": {
        "edit": "deny", "bash": "allow", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "allow",
        "external_directory": "allow", "todowrite": "allow",
        "webfetch": "allow", "websearch": "allow", "lsp": "allow",
        "skill": {
          "plan": "allow", "read": "allow", "doc-scout": "allow",
          "fact-checker": "allow", "system-tools": "allow"
        },
        "question": "allow", "doom_loop": "allow"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "memory_*": true, "context7_*": true, "web-search_*": true,
        "arxiv_*": true, "pdf_*": true
      }
    },
    "read": {
      "mode": "primary",
      "description": "Pure read-only mode. Minimal access.",
      "temperature": 0.1,
      "prompt": "You are a read-only assistant.",
      "permission": {
        "edit": "deny", "bash": "deny", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "deny",
        "external_directory": "allow", "todowrite": "deny",
        "webfetch": "deny", "websearch": "deny", "lsp": "allow",
        "skill": { "read": "allow", "plan": "allow", "system-tools": "allow" },
        "question": "allow", "doom_loop": "allow"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "pdf_*": true, "arxiv_*": true, "web-search_*": true, "context7_*": true
      }
    },
    "research": {
      "mode": "primary",
      "description": "All research: scientific, web, documentation, fact-checking.",
      "temperature": 0.15,
      "prompt": "You are a research specialist.",
      "permission": {
        "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "allow",
        "external_directory": "allow", "todowrite": "allow",
        "webfetch": "allow", "websearch": "allow", "lsp": "allow",
        "skill": {
          "deep-research": "allow", "scientific-research": "allow",
          "scientific-computing": "allow", "doc-scout": "allow",
          "fact-checker": "allow", "system-tools": "allow"
        },
        "question": "allow", "doom_loop": "ask"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "memory_*": true,
        "arxiv_*": true, "pdf_*": true, "web-search_*": true,
        "context7_*": true, "pubchem_*": true
      }
    },
    "coding": {
      "mode": "primary",
      "description": "Developer. Writes, debugs y refactoriza.",
      "temperature": 0.15,
      "prompt": "You are a Developer specialist.",
      "permission": {
        "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "allow",
        "external_directory": "allow", "todowrite": "allow",
        "webfetch": "allow", "websearch": "allow", "lsp": "allow",
        "skill": {
          "coding": "allow", "refactoring": "allow", "test-writer": "allow",
          "tdd": "allow", "commit-message": "allow",
          "systematic-debugging": "allow", "system-tools": "allow"
        },
        "question": "allow", "doom_loop": "ask"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "git_*": true, "web-search_*": true, "context7_*": true, "pdf_*": true
      }
    },
    "coding-web": {
      "mode": "primary",
      "description": "Web developer. Frontend, backend, APIs.",
      "temperature": 0.15,
      "prompt": "You are a web development specialist.",
      "permission": {
        "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "allow",
        "external_directory": "allow", "todowrite": "allow",
        "webfetch": "allow", "websearch": "allow", "lsp": "allow",
        "skill": {
          "coding": "allow", "refactoring": "allow", "test-writer": "allow",
          "tdd": "allow", "commit-message": "allow",
          "systematic-debugging": "allow", "system-tools": "allow"
        },
        "question": "allow", "doom_loop": "ask"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "playwright_*": true, "web-search_*": true,
        "context7_*": true, "pdf_*": true
      }
    },
    "code-quality": {
      "mode": "primary",
      "description": "Code review, testing, and refactoring.",
      "temperature": 0.15,
      "prompt": "You are a code quality specialist.",
      "permission": {
        "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "allow",
        "external_directory": "allow", "todowrite": "allow",
        "webfetch": "allow", "websearch": "allow", "lsp": "allow",
        "skill": {
          "code-reviewer": "allow", "test-writer": "allow",
          "tdd": "allow", "refactoring": "allow", "system-tools": "allow"
        },
        "question": "allow", "doom_loop": "ask"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "git_*": true, "pdf_*": true
      }
    },
    "build": {
      "mode": "primary",
      "temperature": 0.1,
      "description": "Handles project building and compilation tasks.",
      "prompt": "You are a build specialist.",
      "permission": {
        "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "allow",
        "external_directory": "allow", "todowrite": "allow",
        "webfetch": "allow", "websearch": "allow", "lsp": "allow",
        "skill": {
          "coding": "allow", "refactoring": "allow", "test-writer": "allow",
          "tdd": "allow", "commit-message": "allow",
          "systematic-debugging": "allow", "system-tools": "allow"
        },
        "question": "allow", "doom_loop": "ask"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "git_*": true, "pdf_*": true
      }
    },
    "refactoring": {
      "mode": "primary", "temperature": 0.15,
      "description": "Refactors code improving structure and readability.",
      "prompt": "You are a refactoring specialist. Improve code structure while preserving behavior.",
      "permission": {
        "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "allow",
        "external_directory": "allow", "todowrite": "allow",
        "webfetch": "allow", "websearch": "allow", "lsp": "allow",
        "skill": { "system-tools": "allow", "refactoring": "allow" },
        "question": "allow", "doom_loop": "ask"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "git_*": true, "context7_*": true, "pdf_*": true
      }
    },
    "typescript-dev": {
      "mode": "primary", "temperature": 0.15,
      "description": "TypeScript/JavaScript developer. Frontend, backend, Node.js, React, Next.js.",
      "prompt": "You are a TypeScript/JavaScript developer. Load the coding skill.",
      "permission": {
        "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "allow",
        "external_directory": "allow", "todowrite": "allow",
        "webfetch": "allow", "websearch": "allow", "lsp": "allow",
        "skill": { "coding": "allow", "refactoring": "allow", "test-writer": "allow", "system-tools": "allow" },
        "question": "allow", "doom_loop": "ask"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "git_*": true, "context7_*": true, "web-search_*": true, "pdf_*": true
      }
    },
    "rust-dev": {
      "mode": "primary", "temperature": 0.15,
      "description": "Rust developer. Cargo, crates, systems programming.",
      "prompt": "You are a Rust developer. Load the coding skill.",
      "permission": {
        "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "allow",
        "external_directory": "allow", "todowrite": "allow",
        "webfetch": "allow", "websearch": "allow", "lsp": "allow",
        "skill": { "coding": "allow", "refactoring": "allow", "system-tools": "allow" },
        "question": "allow", "doom_loop": "ask"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "git_*": true, "context7_*": true, "web-search_*": true, "pdf_*": true
      }
    },
    "cpp-dev": {
      "mode": "primary", "temperature": 0.15,
      "description": "C/C++ developer. CMake, Make, systems programming.",
      "prompt": "You are a C/C++ developer. Load the coding skill.",
      "permission": {
        "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow",
        "grep": "allow", "list": "allow", "task": "allow",
        "external_directory": "allow", "todowrite": "allow",
        "webfetch": "allow", "websearch": "allow", "lsp": "allow",
        "skill": { "coding": "allow", "refactoring": "allow", "system-tools": "allow" },
        "question": "allow", "doom_loop": "ask"
      },
      "tools": {
        "memos_*": true,
        "sequential-thinking": true,
        "git_*": true, "context7_*": true, "web-search_*": true, "pdf_*": true
      }
    },
    "compaction": {
      "model": "guzman-lopez/compactador"
    }
  },

  "lsp": {
    "typescript": {
      "command": [
        "{BASE_DIR}/node_modules/.bin/typescript-language-server",
        "--stdio"
      ],
      "extensions": [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"]
    },
    "python": {
      "command": ["pylsp"],
      "extensions": [".py", ".pyi"],
      "initialization": {
        "pylsp": {
          "plugins": {
            "preload": { "enabled": false },
            "pylint": { "enabled": false },
            "mypy_ls": { "enabled": false },
            "jedi_completion": { "resolve_at_most": 5 }
          }
        }
      }
    },
    "cpp": {
      "command": ["clangd"],
      "extensions": [".cpp", ".cxx", ".cc", ".c", ".h", ".hpp", ".hxx"]
    },
    "rust": {
      "command": ["rust-analyzer"],
      "extensions": [".rs"]
    }
  },

  "mcp": {
    "playwright": {
      "type": "local", "enabled": true,
      "command": [
        "{BASE_DIR}/node_modules/.bin/playwright-mcp",
        "--browser", "chromium",
        "--executable-path",
        "{CHROMIUM_PATH}",
        "--no-sandbox"
      ]
    },
    "sequential-thinking": {
      "type": "local", "enabled": true,
      "command": [
        "{BASE_DIR}/node_modules/.bin/mcp-server-sequential-thinking"
      ]
    },
    "memory": {
      "type": "local", "enabled": true,
      "command": [
        "{BASE_DIR}/node_modules/.bin/mcp-server-memory"
      ],
      "env": {
        "MEMORY_FILE_PATH": "{BASE_DIR}/memory/memory.json"
      }
    },
    "context7": {
      "type": "local", "enabled": true,
      "command": ["npx", "-y", "@upstash/context7-mcp"]
    },
    "web-search": {
      "type": "local", "enabled": true,
      "command": [
        "{BASE_DIR}/bin/searxng-mcp.sh"
      ]
    },
    "arxiv": {
      "type": "local", "enabled": true,
      "command": [
        "arxiv-mcp-server",
        "--storage-path", "{HOME}/.arxiv-mcp-server/papers"
      ]
    },
    "pdf": {
      "type": "local", "enabled": true,
      "command": [
        "{BASE_DIR}/node_modules/.bin/pdf-reader-mcp"
      ]
    },
    "git": {
      "type": "local", "enabled": true,
      "command": [
        "{BASE_DIR}/node_modules/.bin/git-mcp-server"
      ]
    },
    "pubchem": {
      "type": "local", "enabled": true,
      "command": [
        "{BASE_DIR}/node_modules/.bin/pubchem-mcp-server"
      ]
    },
    "memos": {
      "type": "remote", "enabled": true,
      "url": "http://217.154.101.35:8443/mcp",
      "headers": {
        "Authorization": "Bearer {MEMOS_TOKEN}"
      }
    }
  },

  "permission": {
    "ruff": "allow",
    "verify-deps": "allow",
    "verify-opencode": "allow",
    "web-search_*": "allow",
    "arxiv_*": "allow",
    "git_*": "allow", "pdf_*": "allow",
    "playwright_*": "allow", "memory_*": "allow",
    "pubchem_*": "allow", "context7_*": "allow",
    "sequential-thinking": "allow",
    "memos_*": "allow",
    "skill": {
      "build": "deny", "plan": "deny", "read": "deny", "yolo": "deny",
      "coding": "deny", "scientific-research": "deny",
      "scientific-computing": "deny", "deep-research": "deny",
      "doc-scout": "deny", "fact-checker": "deny",
      "code-reviewer": "deny", "refactoring": "deny",
      "test-writer": "deny", "tdd": "deny", "commit-message": "deny",
      "systematic-debugging": "deny"
    }
  },

  "tools": {
    "git_*": true, "arxiv_*": true, "pdf_*": true,
    "playwright_*": true, "memory_*": true, "pubchem_*": true,
    "web-search_*": true, "context7_*": true,
    "sequential-thinking": true, "memos_*": true
  }
}
}'''

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  MOTOR DE INSTALACION                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class C:
    R = "\033[0m"; B = "\033[1m"; RED = "\033[91m"; GRN = "\033[92m"
    YEL = "\033[93m"; CYN = "\033[96m"; DIM = "\033[2m"

def log(m, c=C.R): print(f"{c}{m}{C.R}")
def step(n, m): log(f"\n{'='*60}", C.CYN); log(f"  [{n}] {m}", C.B+C.CYN); log(f"{'='*60}", C.CYN)
def ok(m): log(f"  ✓ {m}", C.GRN)
def warn(m): log(f"  ⚠ {m}", C.YEL)
def err(m): log(f"  ✗ {m}", C.RED)
def info(m): log(f"  → {m}", C.DIM)


def write_file(path, content):
    """Escribe un archivo creando directorios padres si es necesario."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    ok(str(path))


def find_chromium_executable():
    """Encuentra el ejecutable de Chromium instalado por Playwright cross-platform.

    Returns:
        Path al ejecutable, o None si no se encuentra.
    """
    if IS_LINUX:
        cache = Path.home() / ".cache" / "ms-playwright"
        subdir_pattern = "chrome-linux*"  # chrome-linux, chrome-linux64
        exe_name = "chrome"
    elif IS_MAC:
        cache = Path.home() / "Library" / "Caches" / "ms-playwright"
        subdir_pattern = "chrome-mac*"
        exe_name = "Chromium"  # macOS usa .app, pero la ruta interna es 'Chromium'
    elif IS_WINDOWS:
        local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        cache = Path(local) / "ms-playwright"
        subdir_pattern = "chrome-win*"
        exe_name = "chrome.exe"
    else:
        return None

    if not cache.exists():
        return None

    # Buscar versión más reciente
    for chromium_dir in sorted(cache.glob(f"chromium-*/{subdir_pattern}"), reverse=True):
        exe_path = chromium_dir / exe_name
        if exe_path.exists():
            return str(exe_path)
        # En macOS, el ejecutable está dentro de .app
        if IS_MAC:
            for app_exe in chromium_dir.glob("Chromium.app/Contents/MacOS/Chromium"):
                return str(app_exe)
    return None


def install_npm(target_dir):
    """Ejecuta npm install."""
    step("NPM", "Instalando dependencias npm (MCP servers)...")
    # Usar shutil.which para detectar node/npm cross-platform
    if shutil.which("node") is None:
        err("Node.js no encontrado. Instala desde https://nodejs.org")
        return False
    if shutil.which("npm") is None:
        err("npm no encontrado. Viene con Node.js — reinstala Node.js desde https://nodejs.org")
        return False

    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
        ok(f"Node.js: {r.stdout.strip()}")
    except Exception:
        err("Node.js no encontrado. Instala desde https://nodejs.org")
        return False

    info("Ejecutando npm install (puede tardar)...")
    try:
        r = subprocess.run(["npm", "install"], cwd=str(target_dir),
                           capture_output=True, text=True, timeout=600)
        if r.returncode == 0:
            ok("npm install completado — MCP servers instalados")
            return True
        else:
            err(f"npm install fallo: {r.stderr[-300:]}")
            return False
    except Exception as e:
        err(f"Error: {e}")
        return False


# ── SearXNG MCP (Python) ──────────────────────────────────────────────────────
SEARXNG_MCP_PY = r'''#!/usr/bin/env python3
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
    # Send initialized notification
    _send({"jsonrpc": "2.0", "method": "initialized"})

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
'''

SEARXNG_MCP_SH = r'''#!/usr/bin/env bash
# Wrapper para searxng-mcp.py
# Carga .env si existe, luego ejecuta el MCP

DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$DIR/.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

exec python3 "$DIR/bin/searxng-mcp.py"
'''


def install_searxng_mcp(target_dir):
    """Instala SearXNG MCP (Python)."""
    step("WEB-SEARCH", "Instalando SearXNG MCP (buscador privado)...")
    bin_dir = target_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Escribir searxng-mcp.py
    py_path = bin_dir / "searxng-mcp.py"
    py_path.write_text(SEARXNG_MCP_PY)
    py_path.chmod(0o755)
    ok(f"{py_path}")

    # Escribir searxng-mcp.sh
    sh_path = bin_dir / "searxng-mcp.sh"
    sh_path.write_text(SEARXNG_MCP_SH)
    sh_path.chmod(0o755)
    ok(f"{sh_path}")

    ok("SearXNG MCP instalado correctamente")
    return True


def install_arxiv_python():
    """Instala arxiv-mcp-server via uv tool install (Python)."""
    step("ARXIV", "Instalando arxiv-mcp-server (Python via uv)...")
    try:
        # Usar shutil.which en lugar de `which` (no existe en Windows)
        if shutil.which("uv") is None:
            info("uv no encontrado, instalando...")
            if IS_WINDOWS:
                # Instalar uv en Windows via PowerShell
                info("  Descargando uv para Windows via PowerShell...")
                r = subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
                     "irm https://astral.sh/uv/install.ps1 | iex"],
                    capture_output=True, text=True, timeout=120
                )
                if r.returncode != 0:
                    err(f"Instalacion de uv fallo: {r.stderr[-300:]}")
                    return False
            else:
                # Unix: curl | sh funciona bien
                r = subprocess.run(
                    "curl -LsSf https://astral.sh/uv/install.sh | sh",
                    shell=True, capture_output=True, text=True, timeout=120
                )
                if r.returncode != 0:
                    err(f"Instalacion de uv fallo: {r.stderr[-300:]}")
                    return False
            # Recargar PATH para incluir uv (puede estar en ~/.cargo/bin o ~/.local/bin)
            # Truco: añadir posibles paths al PATH del proceso actual
            for p in [
                Path.home() / ".cargo" / "bin",
                Path.home() / ".local" / "bin",
                Path(os.environ.get("USERPROFILE", "")) / ".cargo" / "bin" if IS_WINDOWS else None,
            ]:
                if p and p.exists() and str(p) not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = str(p) + os.pathsep + os.environ.get("PATH", "")

        if shutil.which("arxiv-mcp-server") is not None:
            ok("arxiv-mcp-server ya instalado")
            return True

        if shutil.which("uv") is None:
            err("uv no encontrado tras instalacion. Aborta.")
            return False

        info("Ejecutando uv tool install arxiv-mcp-server...")
        r = subprocess.run(["uv", "tool", "install", "arxiv-mcp-server"],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            ok("arxiv-mcp-server instalado correctamente")
            return True
        else:
            err(f"uv tool install fallo: {r.stderr[-200:]}")
            return False
    except Exception as e:
        err(f"Error: {e}")
        return False


def install_system_deps():
    """Detecta e instala dependencias del sistema (comby, bat, etc.)."""
    step("SISTEMA", "Dependencias del sistema...")

    deps = {
        "comby": {
            "check": "comby --version",
            "install": {
                "linux": "yay -S comby-bin  # or: snap install comby",
                "mac": "brew install comby",
                "windows": "choco install comby  # or download from github.com/comby-tools/comby/releases",
            },
        },
        "bat": {
            "check": "bat --version",
            "install": {
                "linux": "sudo pacman -S bat  # or: sudo apt install bat",
                "mac": "brew install bat",
                "windows": "choco install bat",
            },
        },
        "ripgrep": {
            "check": "rg --version",
            "install": {
                "linux": "sudo pacman -S ripgrep  # or: sudo apt install ripgrep",
                "mac": "brew install ripgrep",
                "windows": "choco install ripgrep",
            },
        },
        "fd": {
            "check": "fd --version",
            "install": {
                "linux": "sudo pacman -S fd  # or: sudo apt install fd-find",
                "mac": "brew install fd",
                "windows": "choco install fd",
            },
        },
        "clangd": {
            "check": "clangd --version",
            "install": {
                "linux": "sudo pacman -S clang  # clangd included, or: sudo apt install clangd",
                "mac": "brew install llvm",
                "windows": "choco install llvm  # or from https://releases.llvm.org/",
            },
        },
        "rust-analyzer": {
            "check": "rust-analyzer --version",
            "install": {
                "linux": "rustup component add rust-analyzer  # or: sudo pacman -S rust-analyzer",
                "mac": "rustup component add rust-analyzer",
                "windows": "rustup component add rust-analyzer",
            },
        },
    }

    found = []
    missing = []

    for name, dep in deps.items():
        try:
            r = subprocess.run(
                f"bash -c '{dep['check']}' 2>/dev/null" if not IS_WINDOWS else f"cmd /c {dep['check']} 2>nul",
                shell=True, capture_output=True, timeout=10
            )
            if r.returncode == 0:
                found.append(name)
                ok(f"{name}: {r.stdout.strip().split(chr(10))[0][:50]}")
                # NOTA: chr(10) = '\n' (Pyright lo marca como "str" en vez de "ReadableBuffer" — falso positivo)
            else:
                missing.append(name)
        except Exception:
            missing.append(name)

    if missing:
        warn(f"Faltan: {', '.join(missing)}")
        for name in missing:
            install_cmd = deps[name]["install"].get(OS_NAME, "Ver documentacion oficial")
            info(f"  Instalar {name}: {install_cmd}")
    else:
        ok("Todas las dependencias del sistema encontradas")

    return len(missing) == 0


def install_python_deps():
    """Instala paquetes Python necesarios (ruff, plotext, pylsp)."""
    step("PYTHON", "Paquetes Python...")

    packages = {
        "ruff": "ruff --version",
        "plotext": "python3 -c 'import plotext; print(plotext.__version__)'",
        "python-lsp-server": "pylsp --version",
    }

    found = []
    missing = []

    for pkg, check_cmd in packages.items():
        try:
            r = subprocess.run(
                f"bash -c '{check_cmd}'" if not IS_WINDOWS else f"cmd /c {check_cmd}",
                shell=True, capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0:
                found.append(pkg)
                ok(f"{pkg}: {r.stdout.strip()[:40]}")
            else:
                missing.append(pkg)
        except Exception:
            missing.append(pkg)

    if missing:
        warn(f"Faltan: {', '.join(missing)}")
        for pkg in missing:
            info(f"  Instalar: pip install {pkg}  (o: uv pip install {pkg})")
    else:
        ok("Todos los paquetes Python encontrados")

    return len(missing) == 0


def install_playwright():
    """Instala navegadores de Playwright."""
    step("PLAYWRIGHT", "Navegadores...")

    if IS_WINDOWS:
        local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        cache = Path(local) / "ms-playwright"
    elif IS_MAC:
        cache = Path.home() / "Library" / "Caches" / "ms-playwright"
    else:
        cache = Path.home() / ".cache" / "ms-playwright"

    if cache.exists() and any(cache.iterdir()):
        ok(f"Navegadores ya instalados en {cache}")
        return True

    info("Instalando Chromium via Playwright...")
    try:
        r = subprocess.run(
            ["npx", "playwright", "install", "chromium"],
            capture_output=True, text=True, timeout=300
        )
        if r.returncode == 0:
            ok("Chromium instalado via Playwright")
            return True
        else:
            warn("No se pudo instalar Chromium automaticamente")
            info("  Instalar manualmente: npx playwright install chromium")
            return True  # No critico
    except Exception as e:
        warn(f"Error: {e}")
        info("  Se instalara bajo demanda al usar opencode")
        return True  # No critico


def verify_installation(target_dir):
    """Verifica que todo este instalado correctamente."""
    step("VERIFICACION", "Comprobando instalacion...")

    checks = [
        ("opencode.jsonc", target_dir / "opencode.jsonc"),
        ("package.json",  target_dir / "package.json"),
        (".gitignore",    target_dir / ".gitignore"),
        ("tui.json",      target_dir / "tui.json"),
        ("plugins/",      target_dir / "plugins"),
        ("skills/",       target_dir / "skills"),
        ("node_modules/", target_dir / "node_modules"),
        ("bin/searxng-mcp.py", target_dir / "bin" / "searxng-mcp.py"),
        ("bin/searxng-mcp.sh", target_dir / "bin" / "searxng-mcp.sh"),
        (".env.example", target_dir / ".env.example"),
    ]

    all_ok = True
    for name, path in checks:
        if path.exists():
            ok(f"{name}")
        else:
            err(f"{name} — NO ENCONTRADO")
            all_ok = False

    # Contar MCP servers instalados
    bin_dir = target_dir / "node_modules" / ".bin"
    if bin_dir.exists():
        mcp_bins = [f for f in bin_dir.iterdir()
                    if any(k in f.name for k in ["mcp", "playwright", "arxiv", "pdf-reader", "pubchem", "git-mcp"])]
        # Also check bin/searxng-mcp.py (Python-based MCP)
        searxng_path = target_dir / "bin" / "searxng-mcp.py"
        if searxng_path.exists():
            ok("bin/searxng-mcp.py")
        ok(f"MCP servers: {len(mcp_bins)} instalados")

    # Contar plugins y skills
    plugins_dir = target_dir / "plugins"
    skills_dir = target_dir / "skills"
    if plugins_dir.exists():
        plugins = [f for f in plugins_dir.iterdir() if f.suffix == ".ts"]
        ok(f"Plugins: {len(plugins)}")
    if skills_dir.exists():
        skills = [d for d in skills_dir.iterdir() if d.is_dir()]
        ok(f"Skills: {len(skills)}")

    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="opencode Installer — Genera el entorno completo desde cero",
        epilog="""
Ejemplos:
  python3 setup.py                              # Instala en directorio actual
  python3 setup.py --target ~/opencode          # Instala en ruta especifica
  python3 setup.py --api-key "sk-..."           # Pasa la API key
  OPENCODE_API_KEY="sk-..." python3 setup.py    # O por variable de entorno
        """)
    parser.add_argument("--target", "-t", default=".", help="Directorio destino")
    parser.add_argument("--api-key", "-k", default=None, help="API key para chat.guzman-lopez.com")
    parser.add_argument("--skip-npm", action="store_true", help="Omitir npm install")
    parser.add_argument("--skip-system", action="store_true", help="Omitir dependencias del sistema")
    parser.add_argument("--skip-python", action="store_true", help="Omitir paquetes Python")
    parser.add_argument("--skip-playwright", action="store_true", help="Omitir Playwright")
    parser.add_argument("--force", action="store_true", help="Sobreescribir archivos existentes")
    args = parser.parse_args()

    print(f"""{C.CYN}{C.B}
  ╔══════════════════════════════════════════════════════════════╗
  ║         opencode Environment Installer                      ║
  ║         Genera TODO el entorno desde cero                    ║
  ║         Linux · macOS · Windows                              ║
  ╚══════════════════════════════════════════════════════════════╝{C.R}
  {C.DIM}Detectando OS: {OS_NAME}{C.R}""")

    # 1. Directorio destino
    step("1/7", "Resolviendo directorio destino...")
    target = Path(args.target).resolve()
    ok(f"Destino: {target}")

    # 2. API key
    step("2/7", "Resolviendo API key...")
    api_key = args.api_key or os.environ.get("OPENCODE_API_KEY")
    if not api_key:
        existing = target / "opencode.jsonc"
        if existing.exists() and '"apiKey"' in existing.read_text() and "YOUR_API_KEY" not in existing.read_text():
            api_key = "__PRESERVE__"
            ok("API key ya configurada en opencode.jsonc existente")
        else:
            warn("No se proporciono API key")
            api_key = input("  Ingresa tu API key (o Enter para omitir): ").strip() or "YOUR_API_KEY_HERE"
    if api_key != "__PRESERVE__":
        ok(f"API key configurada ({len(api_key)} chars)")

    # 3. Generar opencode.jsonc
    step("3/7", "Generando opencode.jsonc...")
    base_dir = str(target)
    config = OPENCODE_JSONC.replace("{BASE_DIR}", base_dir)
    config = config.replace("{HOME}", str(Path.home()))
    # Detectar ruta de Chromium instalada por Playwright (cross-platform)
    chromium_path = find_chromium_executable()
    if chromium_path:
        config = config.replace("{CHROMIUM_PATH}", chromium_path)
    else:
        # Fallback: dejar vacío (Playwright MCP lo gestionará)
        config = config.replace("{CHROMIUM_PATH}", "")
        warn("Chromium no detectado. Playwright lo instalará bajo demanda al primer uso.")
    if api_key != "__PRESERVE__":
        config = config.replace("{API_KEY}", api_key)
    else:
        existing_key = (target / "opencode.jsonc").read_text()
        import re
        m = re.search(r'"apiKey":\s*"([^"]+)"', existing_key)
        if m:
            config = config.replace("{API_KEY}", m.group(1))
    write_file(target / "opencode.jsonc", config)

    # 4. Generar plugins y skills
    step("4/7", "Generando plugins y skills...")
    for name, content in PLUGINS.items():
        write_file(target / "plugins" / name, content)
    ok(f"{len(PLUGINS)} plugins generados")

    for name, content in SKILLS.items():
        write_file(target / "skills" / name, content)
    ok(f"{len(SKILLS)} skills generados")

    # 5. Generar archivos auxiliares
    write_file(target / "package.json", PACKAGE_JSON)
    write_file(target / ".gitignore", GITIGNORE)
    write_file(target / "tui.json", TUI_JSON)
    # .env.example (nunca sobrescribe .env real)
    env_example = target / ".env.example"
    if not env_example.exists():
        write_file(env_example, DOTENV_EXAMPLE)
    else:
        ok(f"{env_example} ya existe")

    mcp_conf = MCP_CONFIG.replace("SCRIPTS_DIR_PLACEHOLDER", str(target / "mcp" / "scripts"))
    write_file(target / "mcp" / "config.json", mcp_conf)

    # 6. Instalar npm (MCP servers)
    if not args.skip_npm:
        install_npm(target)
    else:
        warn("Omitiendo npm install (--skip-npm)")

    # 7. Instalar SearXNG MCP (buscador web privado)
    if not args.skip_npm:
        install_searxng_mcp(target)
    else:
        warn("Omitiendo SearXNG MCP (--skip-npm)")

    # Reemplazar placeholders de tokens (avisar si faltan)
    config_path = target / "opencode.jsonc"
    config_text = config_path.read_text()
    if "{MEMOS_TOKEN}" in config_text:
        memos_token = os.environ.get("MEMOS_TOKEN", "")
        if memos_token:
            config_text = config_text.replace("{MEMOS_TOKEN}", memos_token)
        else:
            config_text = config_text.replace("{MEMOS_TOKEN}", "TU_MEMOS_TOKEN_AQUI")
            warn("MEMOS_TOKEN no configurado. Edita opencode.jsonc manualmente.")
    config_path.write_text(config_text)

    # Crear directorio para memory MCP
    memory_dir = target / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / ".gitkeep").touch()
    ok("Directorio memory/ creado")

    # 8. arxiv-mcp-server (Python via uv)
    if not args.skip_npm:
        install_arxiv_python()

    # 9. Dependencias del sistema
    if not args.skip_system:
        install_system_deps()
    else:
        warn("Omitiendo dependencias del sistema (--skip-system)")

    # 10. Paquetes Python
    if not args.skip_python:
        install_python_deps()
    else:
        warn("Omitiendo paquetes Python (--skip-python)")

    # 11. Playwright
    if not args.skip_playwright:
        install_playwright()
    else:
        warn("Omitiendo Playwright (--skip-playwright)")

    # 12. Verificacion final
    verify_installation(target)

    # Resumen
    print(f"""{C.GRN}{C.B}
  ╔══════════════════════════════════════════════════════════════╗
  ║         ✓ Instalacion completada                            ║
  ╚══════════════════════════════════════════════════════════════╝{C.R}
  {C.CYN}Directorio:{C.R}  {target}
  {C.CYN}Config:{C.R}      {target}/opencode.jsonc
  {C.CYN}Plugins:{C.R}     {target}/plugins/  ({len(PLUGINS)} archivos)
  {C.CYN}Skills:{C.R}      {target}/skills/   ({len(SKILLS)} archivos)
  {C.CYN}MCP:{C.R}         {target}/mcp/ + node_modules/

  {C.YEL}Para usar:{C.R}  cd {target} && opencode
  {C.DIM}opencode.jsonc NO se commitea (excluido en .gitignore){C.R}
""")


if __name__ == "__main__":
    main()
