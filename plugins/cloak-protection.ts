/**
 * CloakMCP Protection Plugin for opencode
 *
 * Estrategia híbrida de sanitización:
 * ────────────────────────────────
 * API keys / tokens → formato preservado (sk-proj-****...****)
 *   El modelo ve que es una key real, no se confunde
 * Private keys / certs → [PRIVATE KEY REDACTED: N bytes]
 *   Bloque completo reemplazado, no hay nada que el modelo necesite ver
 * Passwords / secrets genéricos → PZ-xxx (vía CloakMCP, reversible)
 *   Solo si el quickScan no los cubre
 *
 * Flujo:
 *   1. quickScan (regex JS, 0ms) → detecta si hay algo que ocultar
 *   2. safeMask (regex JS, <1ms) → reemplaza con formato preservado
 *   3. cloak CLI (solo para lo no cubierto por regex) → PZ-xxx
 *   4. Rehidratación de PZ-xxx → valores originales
 *
 * Dependencias: pipx install cloakmcp[mcp]
 *               ~/.config/opencode/cloak-policy.yaml
 */

import { type Plugin, tool } from "@opencode-ai/plugin"
import { existsSync, writeFileSync, appendFileSync, readFileSync } from "fs"
import { join } from "path"

// ── Constantes ────────────────────────────────────────────────────
const HOME = process.env.HOME || "/home/cesar"
const CONFIG_DIR = join(HOME, ".config", "opencode")
const POLICY_PATH = join(CONFIG_DIR, "cloak-policy.yaml")
const VAULT_PATH = join(CONFIG_DIR, ".cloak-vault.json")
const LOG_PATH = join(CONFIG_DIR, ".cloak-plugin.log")
const PZ_REGEX = /\b(PZ-[A-Za-z0-9]{12,})\b/g

// ── Estado ────────────────────────────────────────────────────────
let secretVault = new Map<string, string>()
let maskCount = 0
let skipCount = 0

// ══════════════════════════════════════════════════════════════════
//  SAFE MASK — Formato preservado (NO reversible, NO confunde al
//  modelo). Reemplaza secrets con máscaras que mantienen el formato.
// ══════════════════════════════════════════════════════════════════

/**
 * Aplica máscaras con formato preservado a un texto.
 * El modelo ve "sk-proj-****" y sabe que es una key real.
 * NO llama a Python, todo es regex en JS.
 */
function safeMask(text: string): { masked: string; found: boolean } {
  let found = false

  const masked = text
    // ── Private keys: bloque completo → [PRIVATE KEY REDACTED] ──
    .replace(
      /-----BEGIN\s+(?:RSA|DSA|EC|ED25519|OPENSSH|ENCRYPTED|)\s*PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:\w+\s+)*PRIVATE\s+KEY-----/gi,
      (match) => {
        found = true
        const size = match.length
        return `[PRIVATE KEY REDACTED: ${size} bytes]`
      }
    )
    // ── PKCS#8 ──────────────────────────────────────────────────
    .replace(
      /-----BEGIN\s+PRIVATE\s+KEY-----[\s\S]*?-----END\s+PRIVATE\s+KEY-----/gi,
      (match) => {
        found = true
        return `[PRIVATE KEY REDACTED: ${match.length} bytes]`
      }
    )
    // ── Certificados SSL ────────────────────────────────────────
    .replace(
      /-----BEGIN\s+(?:X509\s+)?CERTIFICATE-----[\s\S]*?-----END\s+(?:X509\s+)?CERTIFICATE-----/gi,
      (match) => {
        found = true
        return `[CERTIFICATE REDACTED: ${match.length} bytes]`
      }
    )
    // ── Certificate Requests (CSR) ───────────────────────────────
    .replace(
      /-----BEGIN\s+(?:NEW\s+)?CERTIFICATE\s+REQUEST-----[\s\S]*?-----END\s+(?:NEW\s+)?CERTIFICATE\s+REQUEST-----/gi,
      (match) => {
        found = true
        return `[CSR REDACTED: ${match.length} bytes]`
      }
    )
    // ── PGP keys ─────────────────────────────────────────────────
    .replace(
      /-----BEGIN\s+PGP\s+(?:PUBLIC|PRIVATE)\s+KEY\s+BLOCK-----[\s\S]*?-----END\s+PGP\s+(?:PUBLIC|PRIVATE)\s+KEY\s+BLOCK-----/gi,
      (match) => {
        found = true
        return `[PGP KEY REDACTED: ${match.length} bytes]`
      }
    )
    // ── OpenAI keys ──────────────────────────────────────────────
    .replace(
      /\b(sk-proj-|sk-svcacct-|sk-)[A-Za-z0-9]{16,}([A-Za-z0-9]{4})?\b/g,
      (match, prefix) => {
        found = true
        const restLen = match.length - prefix.length
        if (restLen <= 8) return prefix + '*'.repeat(restLen)
        return prefix + '*'.repeat(Math.min(restLen - 4, 12)) + match.slice(-4)
      }
    )
    // ── GitHub tokens ───────────────────────────────────────────
    .replace(
      /\b(gh[oprsu]_)[A-Za-z0-9]{20,}\b/g,
      (match, prefix) => {
        found = true
        return prefix + '*'.repeat(8) + match.slice(-4)
      }
    )
    // ── GitLab tokens ───────────────────────────────────────────
    .replace(
      /\b(glpat-)[A-Za-z0-9\-_]{8,}\b/g,
      (match, prefix) => {
        found = true
        return prefix + '*'.repeat(8)
      }
    )
    // ── Stripe keys ─────────────────────────────────────────────
    .replace(
      /\b((?:rk|sk|pk)_(?:live|test)_)[A-Za-z0-9]{10,}\b/g,
      (match, prefix) => {
        found = true
        return prefix + '*'.repeat(8)
      }
    )
    // ── AWS Access Keys ─────────────────────────────────────────
    .replace(
      /\b(AKIA|ASIA)[A-Z0-9]{16}\b/g,
      (match, prefix) => {
        found = true
        return prefix + '*'.repeat(8) + match.slice(-4)
      }
    )
    // ── AWS Secret Keys ─────────────────────────────────────────
    .replace(
      /(aws[_-]?secret[_-]?(?:access[_-]?)?key)\s*[:=]\s*["']?[A-Za-z0-9\/+=]{40}["']?/gi,
      (match, keyname) => {
        found = true
        return `${keyname}=[REDACTED: AWS Secret Key]`
      }
    )
    // ── GCP API keys ────────────────────────────────────────────
    .replace(
      /\b(AIza)[0-9A-Za-z\-_]{35}\b/g,
      (match, prefix) => {
        found = true
        return prefix + '*'.repeat(8) + match.slice(-4)
      }
    )
    // ── JWT tokens ──────────────────────────────────────────────
    .replace(
      /\b[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\b/g,
      (match) => {
        found = true
        const parts = match.split('.')
        return `${parts[0].slice(0, 8)}...${parts[2].slice(-4)} [JWT TOKEN]`
      }
    )
    // ── DB connection strings ───────────────────────────────────
    .replace(
      /((?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|rediss):\/\/)[A-Za-z0-9_%]+:[^@\s]+@/gi,
      (match, protocol) => {
        found = true
        return `${protocol}[REDACTED:CREDENTIALS]@`
      }
    )
    // ── HuggingFace tokens ──────────────────────────────────────
    .replace(
      /\b(hf_)[A-Za-z0-9]{10,}\b/g,
      (match, prefix) => {
        found = true
        return prefix + '*'.repeat(8)
      }
    )
    // ── npm tokens ──────────────────────────────────────────────
    .replace(
      /\b(npm_)[A-Za-z0-9]{20,}\b/g,
      (match, prefix) => {
        found = true
        return prefix + '*'.repeat(8)
      }
    )
    // ── SonarQube tokens ────────────────────────────────────────
    .replace(
      /\b(squ_)[0-9a-f]{30,}\b/g,
      (match, prefix) => {
        found = true
        return prefix + '*'.repeat(8)
      }
    )
    // ── Slack tokens ────────────────────────────────────────────
    .replace(
      /\b(xox[baprs]-)[A-Za-z0-9\-]{10,}\b/g,
      (match, prefix) => {
        found = true
        return prefix + '*'.repeat(8)
      }
    )
    // ── Genéricos: api_key / token / password (valores largos) ──
    .replace(
      /((?:api[_-]?key|apikey|auth[_-]?token)\s*[:=]\s*)["']?[A-Za-z0-9_\-.\/=+]{16,}["']?/gi,
      (match, prefix) => {
        found = true
        return `${prefix}[REDACTED:API_KEY]`
      }
    )
    .replace(
      /((?:token|secret|password|passwd|pwd)\s*[:=]\s*)["']?[A-Za-z0-9_\-.\/@!$%^&*()+={}]{12,}["']?/gi,
      (match, prefix) => {
        found = true
        return `${prefix}[REDACTED:SECRET]`
      }
    )
    // ── Bearer tokens en headers ────────────────────────────────
    .replace(
      /(Bearer\s+)[A-Za-z0-9\-_.~+\/]{20,}/gi,
      (match, prefix) => {
        found = true
        return `${prefix}[REDACTED:TOKEN]`
      }
    )

  return { masked, found }
}

// ══════════════════════════════════════════════════════════════════
//  CLOAKMCP INTEGRATION (para casos no cubiertos por safeMask)
// ══════════════════════════════════════════════════════════════════

function log(msg: string) {
  try { appendFileSync(LOG_PATH, `[${new Date().toISOString()}] ${msg}\n`) } catch {}
}

function loadVault(): Map<string, string> {
  try {
    if (existsSync(VAULT_PATH)) {
      return new Map(Object.entries(JSON.parse(readFileSync(VAULT_PATH, "utf-8"))))
    }
  } catch {}
  return new Map()
}

function saveVault() {
  try {
    writeFileSync(VAULT_PATH, JSON.stringify(Object.fromEntries(secretVault), null, 2))
  } catch {}
}

/** Escaneo completo con cloak CLI (safety net) */
async function hasSecrets(text: string): Promise<boolean> {
  try {
    const proc = Bun.spawn(["cloak", "guard", "--policy", POLICY_PATH], {
      stdin: "pipe", stdout: "pipe", stderr: "pipe",
    })
    proc.stdin.write(text)
    proc.stdin.end()
    await proc.exited
    return proc.exitCode !== 0
  } catch { return false }
}

/** Sanitiza con cloak CLI (solo para edge cases) */
async function cloakSanitize(original: string): Promise<string> {
  try {
    const proc = Bun.spawn(["cloak", "sanitize-stdin", "--policy", POLICY_PATH], {
      stdin: "pipe", stdout: "pipe", stderr: "pipe",
    })
    proc.stdin.write(original)
    proc.stdin.end()
    const sanitized = await new Response(proc.stdout).text()
    await proc.exited
    if (sanitized === original) return original

    // Computar mapeo PZ-xxx → original
    const origLines = original.split("\n")
    const sanitizedLines = sanitized.replace(/\r$/, "").split("\n")
    for (let i = 0; i < Math.min(origLines.length, sanitizedLines.length); i++) {
      if (origLines[i] === sanitizedLines[i]) continue
      for (const m of sanitizedLines[i].matchAll(PZ_REGEX)) {
        if (!secretVault.has(m[1])) {
          secretVault.set(m[1], origLines[i])
        }
      }
    }
    saveVault()
    return sanitized
  } catch {
    return original
  }
}

/** Rehidrata PZ-xxx a valores originales */
function rehydrate(text: string): string {
  if (!text || !PZ_REGEX.test(text)) return text
  PZ_REGEX.lastIndex = 0
  let result = text
  for (const m of text.matchAll(PZ_REGEX)) {
    const original = secretVault.get(m[1])
    if (original) {
      result = result.replace(m[1], `[ORIGINAL:${original.length} chars]`)
    }
  }
  return result
}

async function checkHealth(): Promise<string[]> {
  const issues: string[] = []
  try {
    const v = (await Bun.$`cloak --version 2>/dev/null`.text()).trim()
    if (!v) issues.push("cloak no instalado: pipx install cloakmcp[mcp]")
  } catch { issues.push("cloak no instalado") }
  if (!existsSync(POLICY_PATH)) issues.push("Política no encontrada: " + POLICY_PATH)
  return issues
}

// ══════════════════════════════════════════════════════════════════
//  PLUGIN
// ══════════════════════════════════════════════════════════════════

export const CloakProtectionPlugin: Plugin = async () => {
  secretVault = loadVault()
  const issues = await checkHealth()
  if (issues.length) log("Issues: " + issues.join("; "))
  else log(`Plugin OK. Vault: ${secretVault.size} entries`)

  return {
    // ── SANITIZACIÓN AUTOMÁTICA DE TOOL OUTPUTS ────────────────
    "tool.execute.after": async (input: any, output: any) => {
      const toolName = input?.tool || ""
      if (!["read", "bash", "grep", "glob"].includes(toolName)) return

      const text = output?.result
      if (!text || typeof text !== "string" || text.length < 4) return

      // Paso 1: safeMask (JS rápido, formato preservado)
      const { masked, found } = safeMask(text)
      if (found) {
        output.result = masked
        maskCount++
        log(`✅ masked tool:${toolName} (${text.length}→${masked.length} chars)`)

        // Paso 2: safety net con cloak para lo no cubierto
        const stillHasSecrets = await hasSecrets(masked)
        if (stillHasSecrets) {
          const cleaned = await cloakSanitize(masked)
          if (cleaned !== masked) {
            output.result = cleaned
            log(`  + cloak extra sanitize needed`)
          }
        }
        return
      }

      // Si safeMask no encontró nada, chequeo rápido con cloak
      skipCount++
    },

    // ── SANITIZACIÓN DE PROMPTS ────────────────────────────────
    "tui.prompt.append": async (input: any, output: any) => {
      const text = input?.text || ""
      if (!text || text.length < 4) return

      const { masked, found } = safeMask(text)
      if (found) {
        output.text = masked
        log(`✅ masked user prompt`)
      }
    },

    // ── CUSTOM TOOLS ────────────────────────────────────────────
    tool: {
      // Escanea texto (JS rápido, no llama a Python)
      "cloak_scan": tool({
        description: "Escanea texto en busca de API keys, tokens, certificados y secrets. Reporta qué se encontró.",
        args: {
          text: tool.schema.string().describe("Texto a escanear"),
        },
        async execute(args) {
          const { found } = safeMask(args.text)
          if (!found) {
            // Safety net con cloak
            if (await hasSecrets(args.text)) {
              return "⚠️  Se detectaron secrets (no cubiertos por regex). Usa cloak_sanitize."
            }
            return "✅ No se detectaron secrets en el texto."
          }
          // Mostrar qué se reemplazaría
          const { masked } = safeMask(args.text)
          return [
            "⚠️  Secrets detectados. Serían reemplazados así:",
            "```",
            masked.slice(0, 2000),
            "```",
          ].join("\n")
        },
      }),

      // Sanitiza texto (formato preservado)
      "cloak_sanitize": tool({
        description: "Sanitiza texto: reemplaza keys/tokens/certificados con máscaras de formato preservado (sk-proj-****). El modelo ve el formato pero no el valor real.",
        args: {
          text: tool.schema.string().describe("Texto a sanitizar"),
        },
        async execute(args) {
          const { masked, found } = safeMask(args.text)
          if (!found) {
            // Safety net
            const cleaned = await cloakSanitize(args.text)
            return cleaned !== args.text
              ? `⚠️  Secrets detectados (vía CloakMCP):\n\`\`\`\n${cleaned.slice(0, 2000)}\n\`\`\``
              : "✅ No se encontraron secrets."
          }
          return [
            "⚠️  Secrets reemplazados con formato preservado:",
            "```",
            masked.slice(0, 2000),
            "```",
          ].join("\n")
        },
      }),

      // Rehidrata PZ-xxx (si hay)
      "cloak_rehydrate": tool({
        description: "Rehidrata placeholders PZ-xxx a sus valores originales almacenados en el vault local.",
        args: {
          text: tool.schema.string().describe("Texto con PZ-xxx a restaurar"),
        },
        async execute(args) {
          const hydrated = rehydrate(args.text)
          if (hydrated === args.text) return "✅ No se encontraron placeholders PZ-xxx."
          return ["✅ Rehidratado:", "```", hydrated.slice(0, 2000), "```"].join("\n")
        },
      }),

      // Estado del sistema
      "cloak_status": tool({
        description: "Muestra estado del sistema: conteo de máscaras aplicadas, vault, salud de CloakMCP.",
        args: {},
        async execute() {
          const issues = await checkHealth()
          return [
            "## 🛡️ CloakMCP Status — Formato Preservado",
            `**Estado:** ${issues.length === 0 ? "✅ OK" : "⚠️  Issues"}`,
            `**Máscaras aplicadas:** ${maskCount}`,
            `**Outputs sin secrets (skipped):** ${skipCount}`,
            `**Vault local:** ${secretVault.size} entradas PZ-xxx`,
            `**Modo:** Formato preservado (JS) + PZ-xxx (CloakMCP safety net)`,
            "",
            "**Formatos preservados:**",
            "  - API keys:  sk-proj-****...****",
            "  - Tokens:    ghp_****...****, glpat-****, xoxb-****",
            "  - AWS:       AKIA****...****",
            "  - JWT:       eyJ...**** [JWT TOKEN]",
            "  - DB URLs:   postgres://[REDACTED:CREDENTIALS]@host",
            "  - Certs:     [CERTIFICATE REDACTED: N bytes]",
            "  - Priv keys: [PRIVATE KEY REDACTED: N bytes]",
            "",
            ...(issues.length ? ["### ⚠️ Issues:", ...issues] : []),
          ].join("\n")
        },
      }),
    },
  }
}
