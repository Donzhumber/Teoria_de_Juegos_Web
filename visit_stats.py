# -*- coding: utf-8 -*-
"""
Contador de visitas por sesion de Streamlit: visitantes distintos por IP publica
o, si no hay IP, por huella de navegador (cabeceras), no por session_id de Streamlit.
Geolocalizacion solo con IP publica (ip-api.com). Mapa fuera del expander (Pydeck en sidebar).
"""
from __future__ import annotations

import hashlib
import html
import json
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

_DB_PATH = Path(__file__).resolve().parent / "visitor_stats.sqlite"

_GEO_API_TMPL = "http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,lat,lon"


def _raw_public_ip() -> Optional[str]:
    """IP del cliente si es publica y conocida; None en localhost o detras de proxy sin XFF."""
    ip = st.context.ip_address
    if ip:
        s = str(ip).strip()
        if s in {"::1", "127.0.0.1", "0.0.0.0"}:
            return None
        return s
    try:
        h = st.context.headers
        xff = h.get("x-forwarded-for")
    except Exception:
        xff = None
    if xff:
        part = xff.split(",")[0].strip()
        if part and part not in {"::1", "127.0.0.1", "0.0.0.0"}:
            return part
    return None


def _header_get(name: str) -> str:
    try:
        return (st.context.headers.get(name) or "").strip()
    except Exception:
        return ""


def _visitor_key_material() -> str:
    """
    Material estable para un mismo navegador/equipo sin IP publica.
    Con IP publica: solo la IP (un visitante por IP en esa red).
    """
    rip = _raw_public_ip()
    if rip:
        return "ip:" + rip
    ua = _user_agent() or ""
    lang = _header_get("accept-language")
    enc = _header_get("accept-encoding")
    ch = _header_get("sec-ch-ua")
    plat = _header_get("sec-ch-ua-platform")
    return "fp:" + ua + "\x1e" + lang + "\x1e" + enc + "\x1e" + ch + "\x1e" + plat


def _hash_visitor(key_material: str) -> str:
    return hashlib.sha256(key_material.encode("utf-8")).hexdigest()[:40]


def _user_agent() -> Optional[str]:
    try:
        return st.context.headers.get("user-agent")
    except Exception:
        return None


def _is_mobile_user_agent(ua: Optional[str]) -> bool:
    if not ua:
        return False
    u = ua.lower()
    if "ipad" in u:
        return False
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
        "kindle",
        "silk/",
    )
    return any(t in u for t in tokens)


def _geo_lookup(ip: str) -> Tuple[Optional[str], Optional[str], Optional[float], Optional[float]]:
    if not ip or ip.startswith("::1") or ip.startswith("127."):
        return None, None, None, None
    try:
        safe = urllib.parse.quote(ip, safe=".:[]")
        url = _GEO_API_TMPL.format(ip=safe)
        req = urllib.request.Request(url, headers={"User-Agent": "Nash2x2-visit-stats/1"})
        with urllib.request.urlopen(req, timeout=2.6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return None, None, None, None
    if data.get("status") != "success":
        return None, None, None, None
    lat, lon = data.get("lat"), data.get("lon")
    try:
        lat_f = float(lat) if lat is not None else None
        lon_f = float(lon) if lon is not None else None
    except (TypeError, ValueError):
        lat_f, lon_f = None, None
    cc = data.get("countryCode") or None
    cname = data.get("country") or None
    return cc, cname, lat_f, lon_f


def _ensure_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS visitors (
            ip_hash TEXT NOT NULL PRIMARY KEY,
            is_mobile INTEGER NOT NULL,
            visits INTEGER NOT NULL DEFAULT 0,
            first_seen REAL NOT NULL,
            last_seen REAL NOT NULL
        )
        """
    )
    cur = conn.execute("PRAGMA table_info(visitors)")
    cols = {r[1] for r in cur.fetchall()}
    for col, typ in (
        ("country_code", "TEXT"),
        ("country_name", "TEXT"),
        ("lat", "REAL"),
        ("lon", "REAL"),
    ):
        if col not in cols:
            conn.execute(f"ALTER TABLE visitors ADD COLUMN {col} {typ}")
    conn.commit()


def _record_visit() -> None:
    key_mat = _visitor_key_material()
    v_h = _hash_visitor(key_mat)
    ua = _user_agent()
    mob = 1 if _is_mobile_user_agent(ua) else 0
    now = time.time()
    rip = _raw_public_ip()
    if rip:
        cc, cname, la, lo = _geo_lookup(rip)
    else:
        cc, cname, la, lo = None, None, None, None
    with sqlite3.connect(_DB_PATH, timeout=5.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        _ensure_db(conn)
        conn.execute(
            """
            INSERT INTO visitors (
                ip_hash, is_mobile, visits, first_seen, last_seen,
                country_code, country_name, lat, lon
            )
            VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ip_hash) DO UPDATE SET
                visits = visitors.visits + 1,
                last_seen = excluded.last_seen,
                is_mobile = excluded.is_mobile
            """,
            (v_h, mob, now, now, cc, cname, la, lo),
        )
        conn.commit()


def maybe_record_visit() -> None:
    """Una escritura a BD por sesion de Streamlit (no en cada rerun de widgets)."""
    if st.session_state.get("_visit_stats_recorded"):
        return
    st.session_state._visit_stats_recorded = True
    try:
        _record_visit()
    except Exception:
        st.session_state._visit_stats_recorded = False


def get_stats() -> dict[str, int]:
    if not _DB_PATH.exists():
        return {
            "visitantes_distintos": 0,
            "moviles_distintos": 0,
            "otros_distintos": 0,
            "visitas_totales": 0,
        }
    with sqlite3.connect(_DB_PATH, timeout=5.0) as conn:
        _ensure_db(conn)
        row = conn.execute(
            """
            SELECT
                COUNT(*),
                SUM(CASE WHEN is_mobile = 1 THEN 1 ELSE 0 END),
                SUM(CASE WHEN is_mobile = 0 THEN 1 ELSE 0 END),
                COALESCE(SUM(visits), 0)
            FROM visitors
            """
        ).fetchone()
    n, nm, no, v = row if row else (0, 0, 0, 0)
    return {
        "visitantes_distintos": int(n or 0),
        "moviles_distintos": int(nm or 0),
        "otros_distintos": int(no or 0),
        "visitas_totales": int(v or 0),
    }


def _map_dataframe() -> pd.DataFrame:
    if not _DB_PATH.exists():
        return pd.DataFrame(columns=["lat", "lon", "country"])
    with sqlite3.connect(_DB_PATH, timeout=5.0) as conn:
        _ensure_db(conn)
        rows = conn.execute(
            """
            SELECT lat, lon, COALESCE(country_name, country_code, '?') AS country
            FROM visitors
            WHERE lat IS NOT NULL AND lon IS NOT NULL
            """
        ).fetchall()
    if not rows:
        return pd.DataFrame(columns=["lat", "lon", "country"])
    df = pd.DataFrame(rows, columns=["lat", "lon", "country"])
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce").astype("float64")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce").astype("float64")
    return df.dropna(subset=["lat", "lon"])


def _country_counts_html() -> str:
    if not _DB_PATH.exists():
        return ""
    with sqlite3.connect(_DB_PATH, timeout=5.0) as conn:
        _ensure_db(conn)
        rows = conn.execute(
            """
            SELECT COALESCE(country_name, country_code, 'Sin dato') AS c, COUNT(*) AS n
            FROM visitors
            GROUP BY COALESCE(country_name, country_code, 'Sin dato')
            ORDER BY n DESC
            LIMIT 8
            """
        ).fetchall()
    if not rows:
        return ""
    parts = [
        f"{html.escape(str(c))}: <strong>{int(n)}</strong>"
        for c, n in rows
    ]
    return " · ".join(parts)


def _render_visit_map_outside_expander() -> None:
    """st.map dentro de st.expander en la barra lateral suele no pintar el mapa (altura 0)."""
    df = _map_dataframe()
    st.markdown(
        '<p class="visit-stats-mini" style="margin:0.25rem 0 0.2rem 0;"><strong>Mapa (origen aprox.)</strong></p>',
        unsafe_allow_html=True,
    )
    if len(df) == 0:
        st.markdown(
            '<p class="visit-stats-mini">Sin puntos: hace falta IP publica y geolocalizacion '
            "(o datos antiguos sin coordenadas). En local suele usarse huella de navegador sin mapa.</p>",
            unsafe_allow_html=True,
        )
        return
    cc_h = _country_counts_html()
    if cc_h:
        st.markdown(
            f'<p class="visit-stats-mini">{cc_h}</p>',
            unsafe_allow_html=True,
        )
    plot_df = df[["lat", "lon"]].copy()
    st.map(
        plot_df,
        latitude="lat",
        longitude="lon",
        use_container_width=True,
        height=260,
        zoom=1,
    )


def render_visit_stats_in_sidebar() -> None:
    st.divider()
    st.markdown(
        """
<style>
.visit-stats-mini {
  font-size: 0.68rem;
  line-height: 1.42;
  color: #5c5c5c;
  margin: 0 0 0.35rem 0;
}
.visit-stats-mini strong { font-size: 0.74rem; color: #262730; }
.visit-stats-mini table { font-size: inherit; width: 100%; border-collapse: collapse; }
.visit-stats-mini td { padding: 0.12rem 0; vertical-align: baseline; }
.visit-stats-mini td.num { text-align: right; font-variant-numeric: tabular-nums; }
</style>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Visitas a la pagina", expanded=False):
        s = get_stats()
        st.markdown(
            f"""
<div class="visit-stats-mini">
<table>
<tr><td>Visitantes distintos</td><td class="num"><strong>{s["visitantes_distintos"]}</strong></td></tr>
<tr><td>Movil (distintos)</td><td class="num"><strong>{s["moviles_distintos"]}</strong></td></tr>
<tr><td>Otro (distintos)</td><td class="num"><strong>{s["otros_distintos"]}</strong></td></tr>
<tr><td>Visitas (sesiones Streamlit)</td><td class="num"><strong>{s["visitas_totales"]}</strong></td></tr>
</table>
<p style="margin-top:0.35rem;">
Clave: IP publica si existe; si no, huella estable (User-Agent, idioma, cabeceras sec-ch-ua),
<strong>no</strong> el id de sesion de Streamlit (cambia al recargar). Mapa debajo del expander.
</p>
</div>
            """,
            unsafe_allow_html=True,
        )
    _render_visit_map_outside_expander()
