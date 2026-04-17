#!/bin/bash
# Doble clic: comprueba si otro Mac podra ejecutar el lanzador (Python + Streamlit).
cd "$(dirname "$0")" || exit 1
echo "=== Verificacion Nash BR (carpeta: $(pwd)) ==="
OK=1
if [[ ! -f app.py ]]; then echo "[X] Falta app.py"; OK=0; else echo "[OK] app.py"; fi
if [[ ! -f requirements.txt ]]; then echo "[X] Falta requirements.txt"; OK=0; else echo "[OK] requirements.txt"; fi
if ! command -v python3 >/dev/null 2>&1; then echo "[X] python3 no esta en el PATH"; OK=0; else echo "[OK] python3 -> $(command -v python3)"; fi
if python3 -c "import streamlit" 2>/dev/null; then echo "[OK] paquete streamlit importable"; else echo "[X] Falta streamlit. Ejecute: python3 -m pip install -r requirements.txt"; OK=0; fi
if python3 -c "import matplotlib, numpy" 2>/dev/null; then echo "[OK] matplotlib y numpy"; else echo "[X] Falta matplotlib o numpy"; OK=0; fi
if [[ -d "NashBR Launcher.app" ]]; then echo "[OK] NashBR Launcher.app presente"; else echo "[!] No esta el bundle .app (opcional)"; fi
echo "=============================================="
if [[ "$OK" -eq 1 ]]; then echo "RESULTADO: listo para usar NashBR Launcher.app o Abrir Nash BR.command"; else echo "RESULTADO: corrija los [X] antes de compartir este equipo."; fi
echo ""
read -r -p "Pulse Enter para cerrar..."
