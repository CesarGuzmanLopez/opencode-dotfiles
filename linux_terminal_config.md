# Configuración específica para terminales Linux

## Tu entorno detectado
- **Plataforma**: Linux
- **Directorio de configuración**: ~/.config/opencode/

## Configuración de OpenCode (ya aplicada)
El archivo `~/.config/opencode/tui.json` ya está configurado correctamente.

## Configuración del terminal para Shift+Enter

### GNOME Terminal (Ubuntu/Fedora por defecto)
GNOME Terminal generalmente envía correctamente Shift+Enter. Si no funciona:

1. Abre GNOME Terminal
2. Ve a Perfiles → Preferencias
3. En la pestaña "Atajos de teclado", busca opciones relacionadas con Enter
4. Asegúrate de que no haya atajos que capturen Shift+Enter

### Konsole (KDE)
1. Abre Konsole
2. Ve a Configuración → Configurar Konsole
3. En "Atajos de teclado", verifica que Shift+Enter no esté asignado a otra función

### Alacritty
Alacritty maneja bien las teclas modificadoras por defecto. Si tienes problemas:

1. Edita tu archivo de configuración `~/.config/alacritty/alacritty.yml` o `~/.config/alacritty/alacritty.toml`
2. Asegúrate de que no haya configuraciones personalizadas que interfieran con Shift+Enter

### Kitty
Kitty tiene soporte completo para el protocolo de teclado Kitty:

1. Edita `~/.config/kitty/kitty.conf`
2. Asegúrate de que `keyboard_protocol` esté habilitado (viene por defecto)

### iTerm2 (macOS - si usas WSL desde macOS)
1. Abre iTerm2
2. Ve a Preferences → Profiles → Keys
3. En "General", asegúrate de que "Shift Enter sends Esc [13;2u" esté configurado

## Prueba rápida

Para verificar que tu terminal envía correctamente Shift+Enter:

1. Abre una terminal
2. Ejecuta: `cat -v`
3. Presiona Shift+Enter
4. Deberías ver algo como: `^[13;2u`
5. Presiona Ctrl+C para salir

## Solución de problemas específica para Linux

### Si Shift+Enter no funciona después de configurar OpenCode:

1. **Verificar versión de OpenCode**:
   ```bash
   opencode --version
   ```
   Asegúrate de tener la versión más reciente.

2. **Reiniciar completamente OpenCode**:
   ```bash
   # Matar procesos existentes
   pkill -f opencode
   # Iniciar nuevamente
   opencode
   ```

3. **Verificar configuración**:
   ```bash
   cat ~/.config/opencode/tui.json
   ```

4. **Probar con otro terminal**:
   - Si usas GNOME Terminal, prueba con Konsole o viceversa
   - Esto ayuda a determinar si es problema del terminal específico

### Configuración avanzada (si necesario)

Si necesitas configurar manualmente la secuencia de escape:

1. Identifica qué secuencia envía tu terminal para Shift+Enter
2. Configura el keybind en `tui.json` con esa secuencia específica

## Alternativas en Linux

Si Shift+Enter sigue sin funcionar:

1. **Usa Ctrl+Enter**: Muchos terminales envían correctamente Ctrl+Enter sin configuración adicional
2. **Usa Alt+Enter**: Otra alternativa que suele funcionar
3. **Editor externo**: Presiona `Ctrl+X E` en OpenCode para escribir en tu editor de texto preferido

## Verificación final

Después de cualquier cambio:
1. Guarda la configuración
2. Reinicia OpenCode completamente
3. Prueba Shift+Enter en el prompt
4. Deberías ver una nueva línea sin enviar el mensaje

¡Listo! Ahora deberías poder usar Shift+Enter para crear nuevas líneas en OpenCode.