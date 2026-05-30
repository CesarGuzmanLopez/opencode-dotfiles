import { type Plugin, tool } from "@opencode-ai/plugin"

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
