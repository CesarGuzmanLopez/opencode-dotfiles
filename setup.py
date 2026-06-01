#!/usr/bin/env python3
"""
opencode Environment Installer (Self-Contained)
================================================
Script completamente autónomo. Genera TODO el entorno opencode desde cero.
No necesita archivos externos — todo está embebido.

Uso:
    python3 setup.py                           # Instala en directorio actual
    python3 setup.py --target /ruta/destino    # Instala en ruta específica
    python3 setup.py --api-key TU_LLAVE        # Pasa la API key
    OPENCODE_API_KEY=TU_LLAVE python3 setup.py # O por variable de entorno
"""

import os
import sys
import platform
import subprocess
import argparse
import shutil
from pathlib import Path

# Detectar OS una vez
IS_LINUX   = sys.platform == "linux"
IS_MAC     = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"
OS_NAME    = "linux" if IS_LINUX else ("mac" if IS_MAC else ("windows" if IS_WINDOWS else sys.platform))

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  ARCHIVOS EMBEBIDOS — Todo el proyecto opencode está aquí dentro           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ── package.json ──────────────────────────────────────────────────────────────
PACKAGE_JSON = r'''{
  "name": "opencode-mcp",
  "private": true,
  "type": "module",
  "dependencies": {
    "@cyanheads/arxiv-mcp-server": "latest",
    "@cyanheads/git-mcp-server": "latest",
    "@cyanheads/pubchem-mcp-server": "latest",
    "@modelcontextprotocol/server-filesystem": "latest",
    "@modelcontextprotocol/server-memory": "latest",
    "@modelcontextprotocol/server-puppeteer": "latest",
    "@modelcontextprotocol/server-sequential-thinking": "latest",
    "@opencode-ai/plugin": "1.14.48",
    "@playwright/mcp": "latest",
    "@sylphx/pdf-reader-mcp": "latest",
    "duckduckgo-mcp-server": "latest",
    "mcp-fetch-server": "latest",
    "sonarqube-api-mcp": "^0.2.0",
    "typescript-language-server": "^5.3.0"
  },
  "devDependencies": {
    "@types/bun": "^1.3.14"
  }
}'''

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

# API keys y secrets — NUNCA commitear
opencode.jsonc
.env
.env.*
*.key
*.pem
secrets.json

# Generated files
setup.log
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

PLUGINS["plotext.ts"] = """import { type Plugin, tool } from "@opencode-ai/plugin"

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
data = json.loads('''${args.data}''')
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
"""

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
  "duckduckgo": "duckduckgo-mcp-server",
  "arxiv": "@cyanheads/arxiv-mcp-server",
  "git": "@cyanheads/git-mcp-server",
  "pdf": "@sylphx/pdf-reader-mcp",
  "pubchem": "@cyanheads/pubchem-mcp-server",
  "puppeteer": "@modelcontextprotocol/server-puppeteer",
  "playwright": "@playwright/mcp",
  "sequential-thinking": "@modelcontextprotocol/server-sequential-thinking",
  "memory": "@modelcontextprotocol/server-memory",
  "filesystem": "@modelcontextprotocol/server-filesystem",
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
              results.push(await check(`mcp: ${name}`, `npx -y ${pkg} --version 2>&1`, false, `npx -y ${pkg}`))
            }
          }
          if (args.category === "all" || args.category === "python") {
            results.push(await check("mcp: fetch", `uvx mcp-server-fetch --version 2>&1`, false, `uvx mcp-server-fetch`))
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
          const configPath = home ? `${home}/.config/opencode/opencode.json` : "~/.config/opencode/opencode.json"

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

SKILLS["admin/SKILL.md"] = r'''---
name: admin
description: System setup wizard: installs ALL dependencies, MCPs, and LSPs. Scans project, creates/removes agents and commands.
---
Your job: install ALL tools, create/delete agents, manage MCPs, create commands, and verify everything.

=== AUTO-INITIALIZATION ===
When user says: inicializa / empieza / start / setup / install → run full setup:
1. Detect OS
2. verify-deps(category='all')
3. Install uv, pdftoppm, Node.js deps
4. Ask before each install, use question tool for sudo
5. verify-opencode() at end

=== SYSTEM DEPENDENCIES ===
- comby: structural code search (yay -S comby-bin / brew install comby)
- bat, rg, fd, jq: code search tools (pacman -S / brew install)
- gnuplot, ttyplot: charting tools
- plotext, rich: Python visualization libs (pip install)
- Use verify-deps to check what's installed.
- Load system-tools skill for full reference.

=== AGENT LIFECYCLE ===
- CREATE: ask purpose → generate name/prompt/perms → write to opencode.json → verify-opencode()
- DELETE: confirm → remove from JSON → verify-opencode()
- MODIFY: change prompt/perms/model → verify-opencode()

=== MCP MANAGEMENT ===
- ADD: ask command → add to mcp section → verify-opencode()
- REMOVE: set enabled:false → verify-opencode()

=== PLUGIN CREATION ===
- Use the plugin-creator skill to create new .ts plugin files.
- Plugins go in ~/.config/opencode/plugins/ and are auto-discovered.
- Load the skill: skill({ name: "plugin-creator" })

=== COMMANDS ===
- CREATE: write .md file in ~/.config/opencode/commands/
- Each command has frontmatter: description, usage

=== RULES ===
- After ANY modification → run verify-opencode()
- If verify-opencode fails → REVERT change immediately
- PLATFORM-AWARE: paths differ by OS. Use ~/.local/bin/uvx on Linux, brew on Mac, %APPDATA% on Windows
- Respect PEP 668 on Arch (no system pip, use uv instead)
- SonarQube is optional (needs Docker)
- LSPs are project-dependent, do NOT force at init
'''

SKILLS["coding/SKILL.md"] = r'''---
name: coding
description: General-purpose coding instructions for all coding agents.
---
Available MCPs: ruff, git, pdf, duckduckgo, fetch, arxiv, puppeteer/playwright, sequential-thinking, memory, filesystem.
Also available: comby-search, comby-replace for structural code search and replacement.

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
2. Search each sub-topic with duckduckgo_web_search.
3. Use fetch tools to read top results.
4. List what you found and what gaps remain.
5. Call save-findings with round=1 to persist findings.
6. DO NOT proceed without listing gaps.

ROUND 2 — DIVE:
1. Load findings from round 1 with load-findings.
2. Pick 3-5 most promising results.
3. Use playwright_browser_navigate if page needs JavaScript.
4. Use read_pdf if there are PDF papers.
5. Identify what's still missing.
6. Call save-findings with round=2.

ROUND 3 — ITERATE:
1. Load previous findings.
2. Generate 2-3 new search queries from gaps.
3. Search again with duckduckgo_web_search.
4. For scientific papers: arxiv_search or pubchem_search_compounds.
5. Store key facts with memory_add_observations.
6. Call save-findings with round=3.
7. Assess convergence. If no new info → proceed to verify.

ROUND 4 — VERIFY:
1. Load all previous findings.
2. Each claim needs 2+ independent sources.
3. Check dates — prefer 2025-2026.
4. Flag contradictions explicitly.
5. Call save-findings with round=4.

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
Available: duckduckgo, fetch, playwright, sequential-thinking.

Focus: library/framework API docs, config guides, code examples, release notes, migration guides.

Process:
1. Identify exact library+version
2. Search official docs first
3. Extract function signatures/params/examples
4. Note version.

Rules: prefer official docs over third-party, include version numbers, never invent APIs.
'''

SKILLS["docs-writer/SKILL.md"] = r'''---
name: docs-writer
description: Writes and maintains project documentation. README, API docs, guides, and changelogs.
---
You are a technical writer. Create clear, comprehensive documentation.

Available: duckduckgo, fetch, git, sequential-thinking.

Process:
1. Understand the code/feature by reading the source.
2. Research examples and best practices online.
3. Write documentation following project conventions.

Rules: use clear language, include code examples, explain why not just how, add docstrings for public APIs.
'''

SKILLS["fact-checker/SKILL.md"] = r'''---
name: fact-checker
description: Verifies claims, finds primary sources, checks accuracy of information.
---
Available: duckduckgo, fetch, playwright, sequential-thinking.

Protocol:
1. Identify the claim
2. Search in 2+ independent sources
3. Prioritize: primary sources > official docs > reputable news > expert analysis
4. Check dates, evaluate authority
5. Determine: confirmed / likely true / unverifiable / likely false / debunked

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

SKILLS["plugin-creator/SKILL.md"] = r'''---
name: plugin-creator
description: Creates opencode plugin files (.ts) and places them in the correct directory.
---
## Qué hace esta skill

Crea plugins para opencode y los guarda en `~/.config/opencode/plugins/`.

## Formato de un plugin

```typescript
import { type Plugin, tool } from "@opencode-ai/plugin"

export const MiPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      "mi-tool": tool({
        description: "Descripción",
        args: {
          param: tool.schema.string().describe("Un parámetro"),
        },
        async execute(args, context) {
          const dir = context.worktree || context.directory || "."
          const result = await Bun.$`cd ${dir} && comando ${args.param}`.text()
          return result || "Hecho"
        },
      }),
    },
  }
}
```

## Dónde se guarda

`~/.config/opencode/plugins/<nombre>.ts` — opencode lo descubre automáticamente.

## Cómo habilitarlo para agentes

```json
{
  "tools": { "mi-tool": false },
  "agent": { "build": { "tools": { "mi-tool": true } } }
}
```

## Verificación

```bash
ls ~/.config/opencode/plugins/mi-plugin.ts
cat ~/.local/share/opencode/log/*.log | grep mi-plugin
python3 -m json.tool ~/.config/opencode/opencode.json
opencode mcp ls
```
'''

SKILLS["project-research-code/SKILL.md"] = r'''---
name: project-research-code
description: Code project research: analyzes codebase AND searches internet. Correlates both. Saves report.
---
Split into independent tasks and delegate with task.

1. task({ agent: research-web, task: 'search for best practices on X' })
2. task({ agent: read, task: 'explore project structure for Y' })
3. Each task saves results with save-findings.
4. Collect with load-findings.
5. Correlate findings and compile report.

Protocol: EXPLORE → RESEARCH → CORRELATE → REPORT.
'''

SKILLS["project-research-science/SKILL.md"] = r'''---
name: project-research-science
description: Science project research: finds papers, compounds, resources. No code analysis. Saves report.
---
Available: arxiv, pubchem, pdf, duckduckgo, fetch, playwright, sequential-thinking, memory.

Protocol:
1. SCOPING (domain, terms)
2. LITERATURE SEARCH (arxiv/pubchem)
3. DEEP DETAILS (DOIs/CIDs)
4. SAVE REPORT (./research/)
5. RESPOND.

Rules: This is RESEARCH not code — do NOT use git/grep/code tools. Include DOIs and CIDs. Verify across 2+ sources.
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

SKILLS["security-auditor/SKILL.md"] = r'''---
name: security-auditor
description: Performs security audits: injection flaws, auth issues, data exposure, dependency vulnerabilities.
---
Available: duckduckgo, fetch, git, sequential-thinking.

Focus on:
- OWASP Top 10: injection, broken auth, XSS, insecure deserialization, etc.
- Authentication and authorization flaws
- Data exposure and privacy risks
- Dependency vulnerabilities
- Configuration security issues

Rules: be conservative, flag both confirmed and potential issues, suggest specific fixes.
'''

SKILLS["system-tools/SKILL.md"] = r'''---
name: system-tools
description: Reference of CLI tools useful for AI agents, what they do, and how to install them.
---
Reference of CLI tools useful for AI agents.

## Búsqueda
- rg (ripgrep): buscar texto en archivos
- fd: buscar archivos por nombre
- bat: ver archivos con syntax highlighting
- jq: procesar JSON
- comby: búsqueda estructural de código

## Visualización
- gnuplot: gráficas PNG/SVG
- ttyplot: gráficas en tiempo real
- plotext: gráficas en terminal (Python)
- rich: tablas/árboles con colores (Python)

## Instalación
Arch:  sudo pacman -S <tool>
macOS: brew install <tool>
Debian: sudo apt install <tool>
Python: pip install <tool>

## Plugins relacionados
- bat: muestra archivos con syntax highlighting
- chart: genera gráficas en terminal con plotext
'''

SKILLS["test-writer/SKILL.md"] = r'''---
name: test-writer
description: Writes unit tests, integration tests, and E2E tests. Covers edge cases and mocks.
---
You are a test specialist.

Available: git, playwright, duckduckgo, fetch, sequential-thinking.

Process:
1. Understand the function/module to test.
2. Write tests covering: happy path, edge cases, error states, boundary conditions.
3. Use mocks for external dependencies.
4. Run tests and fix failures.

Rules: each test tests one thing, use descriptive test names, follow project test patterns.
'''

SKILLS["yolo/SKILL.md"] = r'''---
name: yolo
description: YOLO mode. No prompts, no questions, direct execution.
---
Act directly. Read files, make changes, run commands. Do not ask for permission or confirmation. Do not explain your plan. Only output final results and verification steps. Never invent facts.
'''

# ── opencode.jsonc (plantilla) ───────────────────────────────────────────────
# {BASE_DIR} se reemplaza con la ruta real al instalar
# {API_KEY} se reemplaza con la key del usuario

OPENCODE_JSONC = r'''{
  "$schema": "https://opencode.ai/config.json",

  "default_agent": "plan",
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
        "baseURL": "https://chat.guzman-lopez.com/v1",
        "apiKey": "{API_KEY}"
      },
      "models": {
        "pensamiento-profundo-caro": {
          "name": "Pensamiento Profundo",
          "capabilities": { "tools": true, "vision": true, "streaming": true, "function_calling": true, "parallel_tool_calls": true },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "tareas-avanzadas": {
          "name": "Tareas Avanzadas",
          "capabilities": { "tools": true, "vision": true, "streaming": true, "function_calling": true, "parallel_tool_calls": true },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "normal": {
          "name": "Normal",
          "capabilities": { "tools": true, "vision": true, "streaming": true, "function_calling": true, "parallel_tool_calls": true },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "vision": {
          "name": "Visión",
          "capabilities": { "tools": true, "vision": true, "streaming": true, "function_calling": true, "parallel_tool_calls": false },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "normal-gratis": {
          "name": "Normal Gratis",
          "capabilities": { "tools": true, "vision": true, "streaming": true, "function_calling": true, "parallel_tool_calls": true },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "flash": {
          "name": "Flash",
          "capabilities": { "tools": true, "vision": true, "streaming": true, "function_calling": true, "parallel_tool_calls": false },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        },
        "compactador": {
          "name": "Compactador",
          "capabilities": { "tools": false, "vision": true, "streaming": true, "function_calling": false, "parallel_tool_calls": false },
          "modalities": { "input": ["text", "image", "pdf"], "output": ["text"] }
        }
      }
    }
  },

  "agent": {
    "plan": {
      "mode": "primary", "description": "Planning and analysis. Read-only.", "temperature": 0.1,
      "prompt": "You are a senior tech lead for planning. Load the 'plan' skill for full protocol.",
      "permission": { "edit": "deny", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "deny", "websearch": "deny", "lsp": "allow", "skill": { "plan": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "allow" },
      "tools": {}
    },
    "read": {
      "mode": "primary", "description": "Pure read-only mode.", "temperature": 0.1,
      "prompt": "You are a read-only assistant. Load the 'read' skill.",
      "permission": { "edit": "deny", "bash": "deny", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "deny", "external_directory": "allow", "todowrite": "deny", "webfetch": "deny", "websearch": "deny", "lsp": "allow", "skill": { "read": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "allow" },
      "tools": {}
    },
    "yolo": {
      "mode": "primary", "description": "YOLO mode. No prompts, no questions, direct execution.", "temperature": 0.2,
      "prompt": "You are a YOLO mode agent, DO it!",
      "permission": { "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "yolo": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "allow" },
      "tools": {}
    },
    "scientific-research": {
      "mode": "primary", "description": "Academic research: papers, chemical compounds, citations.", "temperature": 0.15,
      "prompt": "You are a scientific researcher. Load the 'scientific-research' skill.",
      "permission": { "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "scientific-research": "allow", "deep-research": "allow", "project-research-science": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "ask", "arxiv_*": "allow", "pubchem_*": "allow", "pdf_*": "allow", "memory_*": "allow" },
      "tools": { "arxiv_*": true, "pubchem_*": true, "pdf_*": true, "memory_*": true, "playwright_*": true, "chart": true, "bat": true, "research-save": true, "save-findings": true, "load-findings": true }
    },
    "project-research-science": {
      "mode": "primary", "description": "Science project research.", "temperature": 0.15,
      "prompt": "You are a science project researcher. Load the 'project-research-science' skill.",
      "permission": { "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "project-research-science": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "ask", "arxiv_*": "allow", "pubchem_*": "allow", "pdf_*": "allow" },
      "tools": { "arxiv_*": true, "pubchem_*": true, "pdf_*": true, "chart": true, "save-findings": true, "load-findings": true }
    },
    "deep-research": {
      "mode": "primary", "description": "Deep iterative research: ALL tools, multi-round research loop.", "temperature": 0.1,
      "prompt": "You are a senior deep research analyst. Load the 'deep-research' skill.",
      "permission": { "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "scientific-research": "allow", "scientific-computing": "allow", "deep-research": "allow", "project-research-science": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "ask", "arxiv_*": "allow", "pubchem_*": "allow", "pdf_*": "allow", "puppeteer_*": "allow", "playwright_*": "allow", "memory_*": "allow" },
      "tools": { "arxiv_*": true, "pubchem_*": true, "pdf_*": true, "memory_*": true, "playwright_*": true, "chart": true, "bat": true, "research-save": true, "save-findings": true, "load-findings": true }
    },
    "doc-scout": {
      "mode": "primary", "description": "Finds technical documentation, API references.", "temperature": 0.2,
      "prompt": "You are a technical documentation specialist. Load the 'doc-scout' skill.",
      "permission": { "edit": "deny", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "doc-scout": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "ask", "puppeteer_*": "allow", "playwright_*": "allow" },
      "tools": { "playwright_*": true, "chart": true, "bat": true, "fetch_*": false, "duckduckgo_*": false }
    },
    "fact-checker": {
      "mode": "primary", "description": "Verifies claims, finds primary sources.", "temperature": 0.1,
      "prompt": "You are a fact-checker. Load the 'fact-checker' skill.",
      "permission": { "edit": "deny", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "fact-checker": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "ask" },
      "tools": { "bat": true }
    },
    "coding": {
      "mode": "primary", "description": "Developer. Writes, debugs y refactoriza.", "temperature": 0.15,
      "prompt": "You are a Developer specialist. Load the coding skill.",
      "permission": { "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "coding": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "ask" },
      "tools": { "ruff": true, "comby-search": true, "comby-replace": true, "git_*": true, "verify-deps": true }
    },
    "coding-web": {
      "mode": "primary", "description": "Web developer. Frontend, backend, APIs, y testing con Playwright.", "temperature": 0.15,
      "prompt": "You are a web development specialist. Load the coding skill.",
      "permission": { "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "coding": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "ask" },
      "tools": { "playwright_*": true, "comby-search": true, "comby-replace": true, "git_*": true, "fetch_*": false, "duckduckgo_*": false, "verify-deps": true }
    },
    "research-web": {
      "mode": "primary", "description": "Web research specialist.", "temperature": 0.2,
      "prompt": "You are a web research specialist. Use duckduckgo, fetch, and playwright to find and extract information from the web.",
      "permission": { "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "doc-scout": "allow", "system-tools": "allow" }, "question": "allow", "doom_loop": "ask" },
      "tools": { "playwright_*": true, "chart": true, "research-save": true, "save-findings": true, "load-findings": true }
    },
    "code-reviewer": {
      "mode": "primary", "temperature": 0.1, "description": "Reviews code for best practices. Read-only.",
      "prompt": "You are a code reviewer. Only analyze code, do not modify.",
      "permission": { "edit": "deny", "bash": "ask", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "system-tools": "allow", "code-reviewer": "allow" }, "question": "allow", "doom_loop": "ask" },
      "tools": { "git_*": true, "verify-deps": true }
    },
    "test-writer": {
      "mode": "primary", "temperature": 0.15, "description": "Writes unit tests, integration tests, and E2E tests.",
      "prompt": "You are a test specialist. Write thorough tests covering relevant scenarios.",
      "permission": { "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "system-tools": "allow", "test-writer": "allow" }, "question": "allow", "doom_loop": "ask" },
      "tools": { "git_*": true, "playwright_*": true, "verify-deps": true }
    },
    "build": {
      "mode": "primary", "temperature": 0.1, "description": "Handles project building and compilation tasks.",
      "prompt": "You are a build specialist. Execute build commands and manage project compilation.",
      "permission": { "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "system-tools": "allow", "verify-deps": "allow" }, "question": "allow", "doom_loop": "ask" },
      "tools": { "verify-deps": true }
    },
    "refactoring": {
      "mode": "primary", "temperature": 0.15, "description": "Refactors code improving structure and readability.",
      "prompt": "You are a refactoring specialist. Improve code structure while preserving behavior.",
      "permission": { "edit": "allow", "bash": "allow", "read": "allow", "glob": "allow", "grep": "allow", "list": "allow", "task": "allow", "external_directory": "allow", "todowrite": "allow", "webfetch": "allow", "websearch": "allow", "lsp": "allow", "skill": { "system-tools": "allow", "refactoring": "allow" }, "question": "allow", "doom_loop": "ask" },
      "tools": { "git_*": true, "comby-search": true, "comby-replace": true, "verify-deps": true, "save-findings": true, "load-findings": true }
    }
  },

  "lsp": {
    "typescript": {
      "command": ["{BASE_DIR}/node_modules/.bin/typescript-language-server", "--stdio"],
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
    }
  },

  "mcp": {
    "playwright": {
      "type": "local", "enabled": true,
      "command": ["{BASE_DIR}/node_modules/.bin/playwright-mcp", "--browser", "chromium"{NO_SANDBOX}]
    },
    "sequential-thinking": {
      "type": "local", "enabled": true,
      "command": ["{BASE_DIR}/node_modules/.bin/mcp-server-sequential-thinking"]
    },
    "memory": {
      "type": "local", "enabled": true,
      "command": ["{BASE_DIR}/node_modules/.bin/mcp-server-memory"]
    },
    "fetch": {
      "type": "local", "enabled": true,
      "command": ["{BASE_DIR}/node_modules/.bin/mcp-fetch-server"]
    },
    "duckduckgo": {
      "type": "local", "enabled": true,
      "command": ["{BASE_DIR}/node_modules/.bin/duckduckgo-mcp-server"]
    },
    "arxiv": {
      "type": "local", "enabled": true,
      "command": ["{BASE_DIR}/node_modules/.bin/arxiv-mcp-server"]
    },
    "pdf": {
      "type": "local", "enabled": true,
      "command": ["{BASE_DIR}/node_modules/.bin/pdf-reader-mcp"]
    },
    "git": {
      "type": "local", "enabled": true,
      "command": ["{BASE_DIR}/node_modules/.bin/git-mcp-server"]
    },
    "pubchem": {
      "type": "local", "enabled": true,
      "command": ["{BASE_DIR}/node_modules/.bin/pubchem-mcp-server"]
    },
    "filesystem": {
      "type": "local", "enabled": true,
      "command": ["{BASE_DIR}/node_modules/.bin/mcp-server-filesystem"]
    }
  },

  "permission": {
    "ruff": "allow",
    "verify-deps": "allow",
    "verify-opencode": "allow",
    "skill": {
      "build": "deny", "plan": "deny", "read": "deny", "research": "deny",
      "yolo": "deny", "admin": "deny", "coding": "deny",
      "scientific-research": "deny", "scientific-computing": "deny",
      "deep-research": "deny", "doc-scout": "deny", "fact-checker": "deny",
      "project-research-code": "deny", "project-research-science": "deny",
      "plugin-creator": "deny"
    }
  },

  "tools": {
    "git_*": false, "arxiv_*": false, "pdf_*": false,
    "puppeteer_*": false, "playwright_*": false,
    "filesystem_*": false, "memory_*": false, "pubchem_*": false
  }
}'''

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  MOTOR DE INSTALACIÓN                                                       ║
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


def install_npm(target_dir):
    """Ejecuta npm install."""
    step("NPM", "Instalando dependencias npm (MCP servers)...")
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
            err(f"npm install falló: {r.stderr[-300:]}")
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
            else:
                missing.append(name)
        except Exception:
            missing.append(name)

    if missing:
        warn(f"Faltan: {', '.join(missing)}")
        for name in missing:
            install_cmd = deps[name]["install"].get(OS_NAME, "Ver documentación oficial")
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
        # Intentar instalar con pip si --install-python fue pasado
        for pkg in missing:
            info(f"  Instalar: pip install {pkg}  (o: uv pip install {pkg})")
    else:
        ok("Todos los paquetes Python encontrados")

    return len(missing) == 0


def install_playwright():
    """Instala navegadores de Playwright."""
    step("PLAYWRIGHT", "Navegadores...")

    # Verificar si ya existen
    cache = Path.home() / ".cache" / "ms-playwright"
    if IS_WINDOWS:
        cache = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
    if IS_MAC:
        cache = Path.home() / "Library" / "Caches" / "ms-playwright"

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
            warn("No se pudo instalar Chromium automáticamente")
            info("  Instalar manualmente: npx playwright install chromium")
            return True  # No crítico
    except Exception as e:
        warn(f"Error: {e}")
        info("  Se instalará bajo demanda al usar opencode")
        return True  # No crítico


def verify_installation(target_dir):
    """Verifica que todo esté instalado correctamente."""
    step("VERIFICACIÓN", "Comprobando instalación...")

    checks = [
        ("opencode.jsonc", target_dir / "opencode.jsonc"),
        ("package.json",  target_dir / "package.json"),
        (".gitignore",    target_dir / ".gitignore"),
        ("tui.json",      target_dir / "tui.json"),
        ("plugins/",      target_dir / "plugins"),
        ("skills/",       target_dir / "skills"),
        ("node_modules/", target_dir / "node_modules"),
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
                    if any(k in f.name for k in ["mcp", "playwright", "duckduck", "arxiv", "pdf-reader", "pubchem", "git-mcp"])]
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
  python3 setup.py --target ~/opencode          # Instala en ruta específica
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
            warn("No se proporcionó API key")
            api_key = input("  Ingresa tu API key (o Enter para omitir): ").strip() or "YOUR_API_KEY_HERE"
    if api_key != "__PRESERVE__":
        ok(f"API key configurada ({len(api_key)} chars)")

    # 3. Generar opencode.jsonc
    step("3/7", "Generando opencode.jsonc...")
    base_dir = str(target)
    config = OPENCODE_JSONC.replace("{BASE_DIR}", base_dir)
    no_sandbox = ', "--no-sandbox"' if IS_LINUX else ""
    config = config.replace("{NO_SANDBOX}", no_sandbox)
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

    mcp_conf = MCP_CONFIG.replace("SCRIPTS_DIR_PLACEHOLDER", str(target / "mcp" / "scripts"))
    write_file(target / "mcp" / "config.json", mcp_conf)

    # 6. Instalar npm (MCP servers)
    if not args.skip_npm:
        install_npm(target)
    else:
        warn("Omitiendo npm install (--skip-npm)")

    # 7. Dependencias del sistema
    if not args.skip_system:
        install_system_deps()
    else:
        warn("Omitiendo dependencias del sistema (--skip-system)")

    # 8. Paquetes Python
    if not args.skip_python:
        install_python_deps()
    else:
        warn("Omitiendo paquetes Python (--skip-python)")

    # 9. Playwright
    if not args.skip_playwright:
        install_playwright()
    else:
        warn("Omitiendo Playwright (--skip-playwright)")

    # 10. Verificación final
    verify_installation(target)

    # Resumen
    print(f"""{C.GRN}{C.B}
  ╔══════════════════════════════════════════════════════════════╗
  ║         ✓ Instalación completada                            ║
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
