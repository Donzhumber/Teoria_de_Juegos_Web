#!/bin/bash
# Todo lo automatizable: sincroniza repo Streamlit, verifica Python, hace commit.
set -e
BASE="$(cd "$(dirname "$0")" && pwd)"
cd "${BASE}"

echo "== 1/3 Sincronizar nash-br-streamlit-solo =="
bash "${BASE}/preparar_repo_para_streamlit.sh"

SOLO="${BASE}/../nash-br-streamlit-solo"
cd "${SOLO}"

echo ""
echo "== 2/3 Verificar imports =="
python3 -c "from game_logic import PayoffMatrix; import streamlit; print('OK:', streamlit.__version__)"

echo ""
echo "== 3/3 Commit en repo local (si hay cambios) =="
git diff --staged --quiet && git diff --quiet || true
if ! git diff --staged --quiet 2>/dev/null || ! git diff --quiet 2>/dev/null; then
	git -c user.email=docente@local -c user.name=Docente commit -m "sync: app Nash 2x2" || true
fi
if git status -s | grep -q .; then
	git -c user.email=docente@local -c user.name=Docente add -A
	git -c user.email=docente@local -c user.name=Docente commit -m "sync: app Nash 2x2" || true
fi
echo "Estado git:"
git status -s || true
git log -1 --oneline 2>/dev/null || true

echo ""
echo "============================================================"
echo "LISTO en este ordenador. Lo que SOLO USTED puede hacer:"
echo "  1) Crear repo vacio en https://github.com/new (publico)"
echo "  2) cd \"${SOLO}\""
echo "     git remote add origin https://github.com/USUARIO/REPO.git"
echo "     git push -u origin main"
echo "  3) https://share.streamlit.io/ -> New app -> ese repo -> app.py -> Deploy"
echo "  4) Pegar la URL .streamlit.app en CODIGO_PARA_ESTUDIANTES.txt"
echo "============================================================"
