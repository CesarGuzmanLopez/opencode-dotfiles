import { type Plugin, tool } from "@opencode-ai/plugin"

const MCP_MAP = {
  "context7": "@upstash/context7-mcp",
  "web-search": "searxng-mcp (Python)",
  "arxiv": "arxiv-mcp-server",
  "pdf": "@sylphx/pdf-reader-mcp",
  "git": "@cyanheads/git-mcp-server",
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
