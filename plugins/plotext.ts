import { type Plugin, tool } from "@opencode-ai/plugin"

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
