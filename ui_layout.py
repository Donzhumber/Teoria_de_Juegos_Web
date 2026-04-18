# -*- coding: utf-8 -*-
"""Deteccion de cliente movil y utilidades de layout (una sola app Streamlit)."""
from __future__ import annotations

from typing import Optional, Union


def _normalize_qp_value(raw: Optional[Union[str, list]]) -> str:
    if raw is None:
        return ""
    if isinstance(raw, list):
        return str(raw[0]).strip().lower() if raw else ""
    return str(raw).strip().lower()


def detect_mobile_client() -> bool:
    """
    True si parece movil/tablet (User-Agent) o si la URL lleva ?m=1 (o m=movil).
    ?m=0 o m=desktop fuerza vista escritorio.
    """
    import streamlit as st

    try:
        raw = st.query_params.get("m")
        s = _normalize_qp_value(raw)
        if s in ("1", "true", "yes", "movil", "mobile"):
            return True
        if s in ("0", "false", "no", "desktop", "web"):
            return False
    except Exception:
        pass

    try:
        ua = (st.context.headers.get("user-agent") or "").lower()
    except Exception:
        return False
    if not ua:
        return False
    if "ipad" in ua or "tablet" in ua:
        return True
    tokens = (
        "mobile",
        "iphone",
        "ipod",
        "android",
        "webos",
        "blackberry",
        "iemobile",
        "opera mini",
        "opera mobi",
        "windows phone",
    )
    return any(t in ua for t in tokens)


def responsive_layout_css() -> str:
    """CSS extra: apila columnas estrechas y reduce padding en pantallas pequenas."""
    return """
/*
 * El ancho util del panel principal baja al abrir la barra lateral, pero las media
 * queries miran el viewport completo. Sin min-width: 0 la cadena flex recorta
 * st.number_input y los numeros de la matriz desaparecen.
 */
.block-container div[data-testid="stHorizontalBlock"] {
  min-width: 0;
}
.block-container div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
  min-width: 0;
}
.block-container div[data-testid="stVerticalBlock"] {
  min-width: 0;
}
.block-container div[data-testid="element-container"] {
  min-width: 0;
}
.block-container div[data-testid="stNumberInput"] {
  min-width: 0;
  max-width: 100%;
}
.block-container div[data-testid="stNumberInput"] input {
  min-width: 0;
}

@media (max-width: 900px) {
  .block-container { padding-left: 0.75rem !important; padding-right: 0.75rem !important; }
  h1 { font-size: 1.35rem !important; }
  /*
   * Apilar columnas en pantallas estrechas, pero NO en bloques que contienen
   * st.number_input (celdas de la matriz): el min-width grande + flex 100%
   * recortaba los inputs y los numeros parecian desaparecer.
   */
  div[data-testid="stHorizontalBlock"]:not(:has([data-testid="stNumberInput"])) {
    flex-wrap: wrap !important;
  }
  div[data-testid="stHorizontalBlock"]:not(:has([data-testid="stNumberInput"]))
    > div[data-testid="column"] {
    min-width: 0 !important;
    flex: 1 1 100% !important;
    max-width: 100% !important;
  }
  div[data-testid="stHorizontalBlock"]:has([data-testid="stNumberInput"]) {
    flex-wrap: nowrap !important;
  }
  div[data-testid="stHorizontalBlock"]:has([data-testid="stNumberInput"])
    > div[data-testid="column"] {
    min-width: 0 !important;
    flex: 1 1 0% !important;
  }
}
"""
