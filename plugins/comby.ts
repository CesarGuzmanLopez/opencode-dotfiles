import { type Plugin, tool } from "@opencode-ai/plugin"

const HELPER = `${process.env.HOME || "~"}/.config/opencode/plugins/comby_helper.py`

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
          const lang = args.language || ""
          const result = await Bun.$`cd ${dir} && python3 ${HELPER} search ${args.template} ${args.path} ${lang}`.text().catch(e => `Error: ${e.message}`)
          return result || "No matches found"
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
          const lang = args.language || ""
          const writeFlag = args.apply ? "false" : "true"
          const result = await Bun.$`cd ${dir} && python3 ${HELPER} replace ${args.template} ${args.replacement} ${args.path} ${lang} ${writeFlag}`.text().catch(e => `Error: ${e.message}`)
          return result || "No replacements made"
        },
      }),
    },
  }
}
