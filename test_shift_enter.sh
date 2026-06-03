#!/bin/bash

# Script de verificación para Shift+Enter en OpenCode
# Autor: Asistente de OpenCode
# Fecha: $(date +%Y-%m-%d)

echo "=== Verificación de configuración Shift+Enter para OpenCode ==="
echo ""

# Verificar si existe el archivo de configuración
if [ -f ~/.config/opencode/tui.json ]; then
    echo "✓ Archivo tui.json encontrado en ~/.config/opencode/"
    
    # Verificar si contiene la configuración de input_newline
    if grep -q "input_newline" ~/.config/opencode/tui.json; then
        echo "✓ Configuración de input_newline presente"
        echo ""
        echo "Contenido actual de tui.json:"
        cat ~/.config/opencode/tui.json
    else
        echo "✗ Configuración de input_newline no encontrada"
        echo "Por favor, agrega la configuración manualmente o ejecuta el script de configuración."
    fi
else
    echo "✗ Archivo tui.json no encontrado en ~/.config/opencode/"
    echo "Por favor, crea el archivo con la configuración adecuada."
fi

echo ""
echo "=== Instrucciones de uso ==="
echo "1. Reinicia OpenCode completamente"
echo "2. Escribe un mensaje en el prompt"
echo "3. Presiona Shift+Enter para agregar una nueva línea"
echo "4. Presiona Enter (o Ctrl+Enter) para enviar el mensaje"
echo ""
echo "=== Solución de problemas ==="
echo "- Si Shift+Enter no funciona, verifica la configuración de tu terminal"
echo "- Consulta SHIFT_ENTER_GUIDE.md para instrucciones específicas del terminal"
echo "- Alternativas: Ctrl+Enter, Alt+Enter, o editor externo (Ctrl+X E)"
echo ""
echo "¡Listo! Disfruta de las nuevas líneas con Shift+Enter en OpenCode."