# Guía: Configurar Shift+Enter para nueva línea en OpenCode

## Configuración ya aplicada

Tu archivo `tui.json` ya está configurado para usar Shift+Enter como nueva línea:

```json
{
  "$schema": "https://opencode.ai/tui.json",
  "theme": "system",
  "keybinds": {
    "input_newline": "shift+enter"
  }
}
```

## Si Shift+Enter no funciona: Configuración del terminal

Algunos terminales no envían correctamente las teclas modificadoras con Enter por defecto. Aquí tienes las soluciones:

### Para Windows Terminal (WSL o CMD/PowerShell)

1. Abre la configuración de Windows Terminal:
   - Presiona `Ctrl+,` en Windows Terminal
   - O navega a: `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`

2. Agrega esto al array "actions" a nivel raíz:
```json
{
  "command": {
    "action": "sendInput",
    "input": "\u001b[13;2u"
  },
  "id": "User.sendInput.ShiftEnterCustom"
}
```

3. Agrega esto al array "keybindings" a nivel raíz:
```json
{
  "keys": "shift+enter",
  "id": "User.sendInput.ShiftEnterCustom"
}
```

4. Guarda y reinicia Windows Terminal

### Para terminales Linux/macOS (iTerm2, GNOME Terminal, etc.)

La mayoría de los terminales modernos ya envían correctamente Shift+Enter. Si no funciona:

1. Verifica si tu terminal soporta el protocolo de teclado Kitty
2. Consulta la documentación de tu terminal sobre la configuración de secuencias de escape para Shift+Enter

## Alternativas si Shift+Enter sigue sin funcionar

- **Ctrl+Enter**: Otra combinación que suele funcionar sin configuración adicional
- **Alt+Enter**: Alternativa adicional
- **Editor externo**: Presiona `Ctrl+X E` para abrir un editor externo donde puedes escribir múltiples líneas cómodamente

## Verificación

1. Reinicia OpenCode completamente
2. Escribe algo en el prompt
3. Presiona Shift+Enter - debería agregar una nueva línea sin enviar el mensaje
4. Presiona Enter (o Ctrl+Enter) para enviar cuando termines

## Solución de problemas

- **No se agrega nueva línea**: Verifica que el terminal esté configurado correctamente (especialmente en Windows)
- **El mensaje se envía igual**: Asegúrate de que no haya otra aplicación capturando el atajo Shift+Enter
- **Error de configuración**: Valida que tu `tui.json` sea JSON válido