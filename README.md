# OpenCode Personal Configuration

This directory (`~/.config/opencode`) holds the user‑specific configuration, plugins, skills, tools, and MCP settings for the [OpenCode](https://opencode.ai) AI coding agent.

## Directory Layout

- `opencode.jsonc` – Main configuration file (JSON with comments).
- `tui.json` – Settings for the terminal UI.
- `plugins/` – TypeScript/JavaScript plugins that extend OpenCode’s capabilities.
- `skills/` – Markdown‑based skill definitions (`* /SKILL.md`) that instruct agents on how to perform tasks.
- `tools/` – Executable TypeScript scripts that the agent can invoke (e.g., dependency verification, linting).
- `mcp/config.json` – Model Context Protocol configuration for connecting to external LLMs/APIs.
- `node_modules/` – Installed npm dependencies for plugins and tools.
- `.ruff_cache/` – Cache used by the Ruff Python linter (auto‑generated, safe to ignore).

## Documentation Links

- **OpenCode Official Documentation**: https://opencode.ai/docs/
- **Plugins Guide**: https://opencode.ai/docs/es/plugins/
- **Skills Reference**: https://opencode.ai/docs/es/skills/
- **Tools & MCP Configuration**: https://opencode.ai/docs/es/configuration/
- **GitHub Repository**: https://github.com/anomalyco/opencode

## Usage

- After cloning this repository into `~/.config/opencode`, run `npm install` (if you plan to develop or modify plugins/tools).
- OpenCode will automatically pick up plugins, skills, and tools from these locations.
- To update the configuration, edit the relevant files and commit changes; the agent will reload them on restart.

## Maintenance

- Backup files (`*.bak`) are not part of the versioned configuration and should be removed.
- Keep this `README.md` up‑to‑date when adding new plugins, skills, or tools.
- To hunt for bugs or inconsistencies in this configuration:
  1. Run `npm install` to ensure all dependencies are satisfied.
  2. Validate JSONC files with a JSONC linter (e.g., using `npm install -g jsonc-eslint-parser` and `eslint opencode.jsonc`).
  3. Check TypeScript plugins/tools for type errors: `npx tsc --noEmit`.
  4. Verify skill markdown files are correctly formatted (no broken links, proper front‑matter if used).
  5. Run any provided test scripts (if present) or invoke the agent in dry‑run mode to see if it loads without errors.
  6. Use `git diff` to review changes before committing.

## License

Personal configuration; no specific license implied.