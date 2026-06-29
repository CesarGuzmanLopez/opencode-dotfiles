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
          // Safe: pass params via a temp JSON file, not interpolated into the script
          const params = JSON.stringify({
            type: args.type,
            data: args.data,
            title: args.title || "",
            xlabel: args.xlabel || "",
            ylabel: args.ylabel || "",
            width: args.width || 80,
          })
          const script = `
import json, sys, os, tempfile
try:
    import plotext as plt
except ImportError:
    print("plotext not installed. Run: pip install plotext")
    sys.exit(0)

params_path = sys.argv[1]
with open(params_path) as f:
    params = json.load(f)

data = json.loads(params["data"])
chart_type = params["type"]
width = params["width"]

if params["title"]:
    plt.title(params["title"])
if params["xlabel"]:
    plt.xlabel(params["xlabel"])
if params["ylabel"]:
    plt.ylabel(params["ylabel"])
plt.plot_size(width, 20)

if chart_type == "bar":
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        plt.bar([d.get("label", str(i)) for i,d in enumerate(data)], [d.get("value", 0) for d in data])
    else:
        plt.bar(range(len(data)), data)
elif chart_type == "line":
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        plt.plot([d.get("label", str(i)) for i,d in enumerate(data)], [d.get("value", 0) for d in data])
    else:
        plt.plot(data)
elif chart_type == "scatter":
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        plt.scatter([d.get("x", i) for i,d in enumerate(data)], [d.get("y", 0) for d in data])
    else:
        plt.scatter(range(len(data)), data)
elif chart_type == "pie":
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        plt.pie([d.get("label", str(i)) for i,d in enumerate(data)], [d.get("value", 0) for d in data])
    else:
        plt.pie([str(i) for i in range(len(data))], data)
plt.show()
os.unlink(params_path)
`
          try {
            const tmpPath = `/tmp/plotext-${Date.now()}.json`
            await Bun.write(tmpPath, params)
            const result = await Bun.$`cd ${dir} && python3 -c ${script} ${tmpPath}`.text()
            return result || "Chart generated"
          } catch (e: any) {
            return `Error: ${e.message}`
          }
        },
      }),
    },
  }
}
