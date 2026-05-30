---
name: plugin-creator
description: Creates opencode plugin files (.ts) and places them in the correct directory.
---
## Qué hace esta skill

Crea plugins para opencode y los guarda en `~/.config/opencode/plugins/`.

## Formato de un plugin

```typescript
import { type Plugin, tool } from "@opencode-ai/plugin"

export const MiPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      "mi-tool": tool({
        description: "Descripción",
        args: {
          param: tool.schema.string().describe("Un parámetro"),
        },
        async execute(args, context) {
          const dir = context.worktree || context.directory || "."
          const result = await Bun.$`cd ${dir} && comando ${args.param}`.text()
          return result || "Hecho"
        },
      }),
    },
  }
}
```

## Dónde se guarda

`~/.config/opencode/plugins/<nombre>.ts` — opencode lo descubre automáticamente.

## Cómo habilitarlo para agentes

```json
{
  "tools": { "mi-tool": false },
  "agent": { "build": { "tools": { "mi-tool": true } } }
}
```

## Verificación

```bash
ls ~/.config/opencode/plugins/mi-plugin.ts
cat ~/.local/share/opencode/log/*.log | grep mi-plugin
python3 -m json.tool ~/.config/opencode/opencode.json
opencode mcp ls
```
