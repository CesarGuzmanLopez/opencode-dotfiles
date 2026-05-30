import { type Plugin, tool } from "@opencode-ai/plugin"

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
