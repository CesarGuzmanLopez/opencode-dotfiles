import { type Plugin, tool } from "@opencode-ai/plugin"

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
          // JSONC has comments, use strip-json-comments then validate with python
          results.push(await check(
            "Config JSONC",
            `python3 -c "
import json, re, sys
with open('${configPath}') as f:
    # Strip single-line comments (JSONC format)
    text = re.sub(r'//.*', '', f.read())
    json.loads(text)
    print('VALID')
" 2>/dev/null || echo 'INVALID'`
          ))
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
