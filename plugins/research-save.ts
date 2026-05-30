import { type Plugin, tool } from "@opencode-ai/plugin"

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
