#!/bin/bash
# Sincroniza la carpeta lista para GitHub / Streamlit Cloud (no borra .git si ya existe).
set -e
ORIGEN="$(cd "$(dirname "$0")" && pwd)"
DEST="${ORIGEN}/../nash-br-streamlit-solo"
echo "Origen:  ${ORIGEN}"
echo "Destino: ${DEST}"
mkdir -p "${DEST}"

for f in app.py game_logic.py requirements.txt; do
	cp -f "${ORIGEN}/${f}" "${DEST}/"
done
[[ -d "${ORIGEN}/.streamlit" ]] && cp -fR "${ORIGEN}/.streamlit" "${DEST}/"
[[ -f "${ORIGEN}/.gitignore" ]] && cp -f "${ORIGEN}/.gitignore" "${DEST}/"
for f in README_PUBLICACION.md PARA_ESTUDIANTES.txt COMO_USAR_EN_OTRO_ORDENADOR.txt CODIGO_PARA_ESTUDIANTES.txt; do
	[[ -f "${ORIGEN}/${f}" ]] && cp -f "${ORIGEN}/${f}" "${DEST}/"
done

(
	cd "${DEST}"
	if [[ ! -d .git ]]; then
		git init -b main
	fi
	git add -A
	git status
)

echo ""
echo "Carpeta lista: ${DEST}"
echo "Siguiente: cd \"${DEST}\" && git commit -am \"sync\"  (si hay cambios)"
echo "Luego: git remote add origin ... && git push -u origin main"
echo "Y en https://share.streamlit.io/ -> New app -> app.py -> Deploy"
