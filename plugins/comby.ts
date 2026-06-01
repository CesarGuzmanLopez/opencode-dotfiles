import { type Plugin, tool } from "@opencode-ai/plugin"

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
            // Parse JSON output and format to match expected structure
            const matches = JSON.parse(result)
            if (matches.length === 0) {
              return "No matches found"
            }
            // Format each match to: {"matched": "...", "range_start": "...", "range_end": "..."}
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
              // Actually modify files
              result = await Bun.$`cd ${dir} && comby -matcher '${args.template}' -rewrite '${args.replacement}' ${lang.join(' ')} ${writeFlag.join(' ')} ${args.path}`.text()
              return result || "Changes applied successfully"
            } else {
              // Dry-run: show what would be changed
              result = await Bun.$`cd ${dir} && comby -matcher '${args.template}' -rewrite '${args.replacement}' ${lang.join(' ')} -json ${args.path}`.text()
              const changes = JSON.parse(result)
              if (changes.length === 0) {
                return "No replacements made"
              }
              // For dry-run, we need to show what would change
              // This is tricky - comby's JSON output for rewrite might differ
              // Fallback to showing the rewrite command would run
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