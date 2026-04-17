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


def _is_public_ip(ip: str) -> bool:
    """True si la IP no es de rangos privados (RFC 1918), localhost o reservada."""
    if not ip or not isinstance(ip, str):
        return False
    s = ip.strip()
    if s in {"::1", "127.0.0.1", "0.0.0.0", "localhost"}:
        return False
    # Filtros basicos para IPv4 privado
    # 10.x.x.x
    if s.startswith("10."):
        return False
    # 192.168.x.x
    if s.startswith("192.168."):
        return False
    # 172.16.x.x - 172.31.x.x
    if s.startswith("172."):
        try:
            second = int(s.split(".")[1])
            if 16 <= second <= 31:
                return False
        except (ValueError, IndexError):
            pass
    # 100.64.x.x (CGNAT)
    if s.startswith("100.64."):
        return False
    # 169.254.x.x (Link-local)
    if s.startswith("169.254."):
        return False
    return True


def _raw_public_ip() -> Optional[str]:
    """Busca en TODAS las cabeceras hasta hallar una IP que pase _is_public_ip."""
    header_names = ("x-forwarded-for", "x-real-ip", "cf-connecting-ip", "client-ip", "forwarded")
    
    try:
        h = st.context.headers
        # 1. Probar nombres conocidos
        for hdr in header_names:
            val = h.get(hdr)
            if val:
                for part in [p.strip() for p in val.split(",")]:
                    if _is_public_ip(part): return part
        
        # 2. Busqueda exhaustiva (por si el nombre varia en mayusculas/minusculas)
        for k, v in h.items():
            k_low = k.lower()
            if any(name in k_low for name in header_names) or "ip" in k_low:
                for part in [p.strip() for p in str(v).split(",")]:
                    if _is_public_ip(part): return part
    except Exception:
        pass

    # 3. Ultimo recurso
    try:
        ip = st.context.ip_address
        if ip and _is_public_ip(str(ip)):
            return str(ip).strip()
    except Exception:
        pass
    return None


def _debug_ip_info() -> str:
    """Retorna un resumen de lo que el sistema ve para diagnostico."""
    try:
        h = st.context.headers
        keys = sorted(list(h.keys()))
        # Solo nombres de cabeceras interesantes
        relevant = [k for k in keys if any(x in k.lower() for x in ("ip", "forw", "proto", "host"))]
        ip_direct = str(st.context.ip_address) if st.context.ip_address else "None"
        return f"Headers: {','.join(relevant)} | IP context: {ip_direct}"
    except Exception as e:
        return f"Error debug: {str(e)}"


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
    """Geolocalizacion con multiples fallbacks."""
    if not ip or ip.startswith("::1") or ip.startswith("127."):
        return None, None, None, None
    
    safe_ip = urllib.parse.quote(ip)

    # Intento 1: ip-api.com (HTTP) - Muy estable para uso gratuito masivo
    try:
        url = f"http://ip-api.com/json/{safe_ip}?fields=status,country,countryCode,lat,lon"
        req = urllib.request.Request(url, headers={"User-Agent": "Nash2x2/1.1"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                lat, lon = data.get("lat"), data.get("lon")
                return (
                    data.get("countryCode"),
                    data.get("country"),
                    (float(lat) if lat is not None else None),
                    (float(lon) if lon is not None else None)
                )
    except Exception:
        pass

    # Intento 2: ipapi.co (HTTPS) - Fallback
    try:
        url = f"https://ipapi.co/{safe_ip}/json/"
        req = urllib.request.Request(url, headers={"User-Agent": "Nash2x2/1.1"})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not data.get("error"):
                lat, lon = data.get("latitude"), data.get("longitude")
                return (
                    data.get("country_code"),
                    data.get("country_name"),
                    (float(lat) if lat is not None else None),
                    (float(lon) if lon is not None else None)
                )
    except Exception:
        pass

    return None, None, None, None


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
        rip = _raw_public_ip()
        dbg = _debug_ip_info()
        msg = (
            f"Sin puntos: IP detectada: {rip[:7] if rip else 'Ninguna'}. "
            f"<br><span style='opacity:0.5'>Debug: {dbg}</span>"
        )
        st.markdown(f'<p class="visit-stats-mini">{msg}</p>', unsafe_allow_html=True)
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
        height=280,
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
