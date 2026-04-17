#!/bin/bash
# Doble clic en Finder: abre Terminal, levanta Streamlit y abre el navegador.
cd "$(dirname "$0")" || exit 1

alert() { echo "$1" >&2; }

abrir_chrome_o_defecto() {
	local url="$1"
	local os_type
	os_type="$(uname -s 2>/dev/null || echo "")"
	if [[ "${os_type}" == "Darwin" ]]; then
		if open -b com.google.Chrome "${url}" 2>/dev/null; then return 0; fi
		for chrome_app in \
			"/Applications/Google Chrome.app" \
			"${HOME}/Applications/Google Chrome.app" \
			"/Applications/Google Chrome Canary.app"; do
			if [[ -d "${chrome_app}" ]]; then
				open -a "${chrome_app}" "${url}" 2>/dev/null && return 0
			fi
		done
		open "${url}" 2>/dev/null && return 0
		return 1
	fi
	if [[ "${os_type}" == "Linux" ]]; then
		for c in google-chrome-stable google-chrome chromium chromium-browser; do
			if command -v "${c}" >/dev/null 2>&1; then
				"${c}" "${url}" 2>/dev/null && return 0
			fi
		done
	fi
	command -v xdg-open >/dev/null 2>&1 && xdg-open "${url}" 2>/dev/null && return 0
	return 1
}

if [[ ! -f "./app.py" ]]; then
	alert "No se encontro app.py en esta carpeta."
	exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
	alert "Instale Python 3."
	exit 1
fi
if ! python3 -c "import streamlit" 2>/dev/null; then
	alert "Ejecute: python3 -m pip install -r requirements.txt"
	exit 1
fi

export MPLCONFIGDIR="${TMPDIR:-/tmp}/mpl-nash-$$"
mkdir -p "$MPLCONFIGDIR"

PORT="${NASH_BR_PORT:-8788}"
URL="http://127.0.0.1:${PORT}/"

EXTRA_ADDR=()
if [[ "${NASH_BR_LAN:-}" == "1" ]]; then
	EXTRA_ADDR=(--server.address "0.0.0.0")
	IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
	echo "Modo LAN: si hay IP, otros PCs pueden usar http://${IP}:${PORT}/"
fi

if command -v lsof >/dev/null 2>&1 && lsof -ti ":${PORT}" >/dev/null 2>&1; then
	lsof -ti ":${PORT}" | xargs kill -9 2>/dev/null || true
	sleep 1
fi

echo "Iniciando Streamlit en ${URL} ..."
python3 -m streamlit run app.py --server.headless true --server.port "${PORT}" --browser.gatherUsageStats false "${EXTRA_ADDR[@]}" &
SPID=$!

for _ in $(seq 1 60); do
	if curl -s -o /dev/null --connect-timeout 1 -w "%{http_code}" "${URL}" 2>/dev/null | grep -q 200; then
		abrir_chrome_o_defecto "${URL}" || open "${URL}"
		echo "Listo. Cierre esta ventana de Terminal para detener el servidor."
		wait "${SPID}"
		exit 0
	fi
	sleep 0.5
done

echo "No se pudo contactar el servidor a tiempo."
kill "${SPID}" 2>/dev/null || true
exit 1
