import { type Plugin, tool } from "@opencode-ai/plugin"

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
