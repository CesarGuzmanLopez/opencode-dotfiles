#!/bin/bash

# Script de diagnóstico para terminales Linux
# Detecta el terminal actual y proporciona instrucciones específicas

echo "=== Diagnóstico de terminal para OpenCode ==="
echo ""

# Detectar el terminal actual
if [ -n "$TERM_PROGRAM" ]; then
    echo "Terminal detectado: $TERM_PROGRAM"
elif [ -n "$TERMINAL_EMULATOR" ]; then
    echo "Terminal detectado: $TERMINAL_EMULATOR"
else
    echo "Terminal no detectado automáticamente"
fi

echo ""

# Verificar variables de entorno relevantes
echo "Variables de entorno del terminal:"
echo "TERM: $TERM"
echo "TERM_PROGRAM: ${TERM_PROGRAM:-no definido}"
echo "COLORTERM: ${COLORTERM:-no definido}"
echo "XDG_SESSION_TYPE: ${XDG_SESSION_TYPE:-no definido}"
echo ""

# Verificar si estamos en un entorno gráfico
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    echo "✓ Entorno gráfico detectado"
else
    echo "✗ Entorno de consola pura (sin interfaz gráfica)"
fi

echo ""

# Verificar la configuración de OpenCode
echo "=== Verificación de configuración OpenCode ==="
if [ -f ~/.config/opencode/tui.json ]; then
    echo "✓ Archivo tui.json encontrado"
    
    # Verificar si contiene input_newline
    if grep -q "input_newline" ~/.config/opencode/tui.json; then
        echo "✓ Configuración input_newline presente"
        echo ""
        echo "Configuración actual:"
        cat ~/.config/opencode/tui.json | grep -A2 -B2 "input_newline"
    else
        echo "✗ Configuración input_newline no encontrada"
    fi
else
    echo "✗ Archivo tui.json no encontrado"
fi

echo ""

# Verificar procesos de OpenCode
echo "=== Procesos de OpenCode ==="
pgrep -la opencode 2>/dev/null || echo "No se encontraron procesos de OpenCode ejecutándose"

echo ""

# Instrucciones específicas por terminal
echo "=== Instrucciones específicas para tu terminal ==="
echo ""

if [ "$TERM_PROGRAM" = "gnome-terminal" ]; then
    echo "Para GNOME Terminal:"
    echo "1. Abre GNOME Terminal"
    echo "2. Ve a Perfiles → Preferencias"
    echo "3. En la pestaña 'Atajos de teclado', verifica que Shift+Enter no esté asignado"
    echo "4. Prueba presionando Shift+Enter en la terminal - debería insertar una nueva línea"
elif [ "$TERM_PROGRAM" = "konsole" ]; then
    echo "Para Konsole:"
    echo "1. Abre Konsole"
    echo "2. Ve a Configuración → Configurar Konsole"
    echo "3. En 'Atajos de teclado', verifica Shift+Enter"
elif [ "$TERM_PROGRAM" = "Alacritty" ] || [ "$TERM" = "alacritty" ]; then
    echo "Para Alacritty:"
    echo "1. Alacritty maneja Shift+Enter correctamente por defecto"
    echo "2. Verifica ~/.config/alacritty/alacritty.toml para configuraciones personalizadas"
elif [ "$TERM_PROGRAM" = "kitty" ] || [ "$TERM" = "xterm-kitty" ]; then
    echo "Para Kitty:"
    echo "1. Kitty soporta completamente el protocolo de teclado Kitty"
    echo "2. Shift+Enter debería funcionar sin configuración adicional"
else
    echo "Terminal genérico detectado:"
    echo "1. La mayoría de los terminales modernos envían Shift+Enter correctamente"
    echo "2. Si no funciona, prueba con Ctrl+Enter o Alt+Enter"
    echo "3. O usa el editor externo con Ctrl+X E en OpenCode"
fi

echo ""

# Comandos de prueba
echo "=== Comandos de prueba ==="
echo "Para verificar que Shift+Enter funciona:"
echo "1. Ejecuta: cat -v"
echo "2. Presiona Shift+Enter"
echo "3. Deberías ver algo como: ^[[13;2u"
echo "4. Presiona Ctrl+C para salir"
echo ""

# Verificar si hay conflictos de teclas
echo "=== Verificación de conflictos potenciales ==="
echo "Si Shift+Enter no funciona, verifica:"
echo "1. Que no haya otra aplicación capturando Shift+Enter"
echo "2. Que la configuración del terminal no esté sobreescribiendo el comportamiento"
echo "3. Que OpenCode esté completamente reiniciado después de los cambios"
echo ""

# Solución rápida
echo "=== Solución rápida ==="
echo "Si necesitas una solución inmediata:"
echo "1. Usa Ctrl+Enter en lugar de Shift+Enter"
echo "2. O presiona Ctrl+X E para abrir el editor externo"
echo "3. Escribe tu mensaje con múltiples líneas en el editor"
echo "4. Guarda y cierra - el mensaje se enviará a OpenCode"
echo ""

echo "¡Diagnóstico completado!"