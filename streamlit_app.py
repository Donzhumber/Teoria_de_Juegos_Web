# -*- coding: utf-8 -*-
"""
Presentacion interactiva: equilibrio de Nash y correspondencias de mejor respuesta (2x2).
Ejecutar: python3 -m streamlit run app.py
"""
from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.lines import Line2D

from ui_layout import detect_mobile_client, responsive_layout_css
from visit_stats import maybe_record_visit, render_visit_stats_in_sidebar

try:
    _MOBILE_UI = detect_mobile_client()
except Exception:
    _MOBILE_UI = False

from game_logic import (
    PayoffMatrix,
    br1_correspondence,
    br2_correspondence,
    expected_u1_A,
    expected_u1_B,
    expected_u2_L,
    expected_u2_R,
    mixed_equilibrium_interior,
    pure_nash_equilibria,
    sample_br1_curve,
    sample_br2_curve,
)

st.set_page_config(
    page_title="Análisis Equilibrio de Nash (2x2)",
    page_icon="",
    layout="centered" if _MOBILE_UI else "wide",
    initial_sidebar_state="collapsed" if _MOBILE_UI else "expanded",
)

# --- ESTILO PARA BLOQUEAR MENÚS DE DESARROLLO + responsive (pantallas estrechas) ---
st.markdown(
    f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    /* No ocultar `header`: ahi va el control para abrir/cerrar la barra lateral (flecha / menu). */
    {responsive_layout_css()}
    </style>
    """,
    unsafe_allow_html=True,
)
if _MOBILE_UI:
    st.caption(
        "Vista movil: pulse **arriba a la izquierda** el icono de menu (flecha) para abrir la barra lateral "
        "(ejemplos de matriz y visitas). `?m=0` en la URL fuerza vista escritorio."
    )

LABEL_ROW = ("A (fila arriba)", "B (fila abajo)")
LABEL_COL = ("L (col. izq.)", "R (col. der.)")

# Nash puro: ancla la etiqueta hacia el *interior* del cuadrado (q,p) para no montarse
# sobre ticks, numeros de ejes ni titulos; ha/va fijan desde que esquina se desplaza la caja.
_PURE_NASH_LABEL_STYLE: dict[
    tuple[float, float],
    tuple[tuple[float, float], str, str],
] = {
    (0.0, 0.0): ((40.0, 44.0), "left", "bottom"),
    (1.0, 0.0): ((-40.0, 44.0), "right", "bottom"),
    (0.0, 1.0): ((40.0, -44.0), "left", "top"),
    (1.0, 1.0): ((-40.0, -44.0), "right", "top"),
}

# Flecha desde la caja de texto hasta el punto (xy); shrink evita que tape el marcador.
_ARROW_NASH_PURO = dict(
    arrowstyle="-|>",
    color="#1b5e20",
    lw=1.5,
    shrinkA=10,
    shrinkB=7,
    mutation_scale=13,
)
_ARROW_NASH_MIXTO = dict(
    arrowstyle="-|>",
    color="#212121",
    lw=1.45,
    shrinkA=8,
    shrinkB=6,
    mutation_scale=13,
)

_NASH_ANN_BBOX = dict(
    boxstyle="round,pad=0.32",
    facecolor="white",
    edgecolor="0.55",
    linewidth=0.75,
    alpha=0.94,
)
_NASH_ANN_BBOX_PURO = dict(
    boxstyle="round,pad=0.32",
    facecolor="white",
    edgecolor="green",
    linewidth=0.85,
    alpha=0.94,
)

PRESETS: dict[str, tuple[float, ...]] = {
    "Coordination (dos Nash puros)": (3.0, 0.0, 0.0, 2.0, 1.0, 0.0, 0.0, 3.0),
    "Dilema del prisionero": (-1.0, -3.0, 0.0, -2.0, -1.0, 0.0, -3.0, -2.0),
    "Cara o sello (equilibrio mixto)": (1.0, -1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0),
    "Batalla de los sexos": (2.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 2.0),
}

_KEYS = ("u1al", "u1ar", "u1bl", "u1br", "u2al", "u2ar", "u2bl", "u2br")
_DEFAULTS = (3.0, 0.0, 0.0, 2.0, 1.0, 0.0, 0.0, 3.0)


def _init_payoffs() -> None:
    for k, v in zip(_KEYS, _DEFAULTS):
        if k not in st.session_state:
            st.session_state[k] = v


_init_payoffs()
maybe_record_visit()

with st.sidebar:
    st.header("Ejemplos")
    preset_name = st.selectbox("Matriz de ejemplo", list(PRESETS.keys()))
    if st.button("Cargar ejemplo seleccionado"):
        for k, v in zip(_KEYS, PRESETS[preset_name]):
            st.session_state[k] = v
        st.rerun()
    render_visit_stats_in_sidebar()


def plot_best_response(
    M: PayoffMatrix,
    q_cursor: Optional[float] = None,
    p_cursor: Optional[float] = None,
    *,
    compact: bool = False,
) -> plt.Figure:
    """Correspondencias BR en (q, p). Si se pasan q_cursor y p_cursor, marca la posicion del usuario."""
    fig, ax = plt.subplots(figsize=(6.4, 7.0) if compact else (7.8, 9.2))

    qs, p_lo, p_hi = sample_br1_curve(M)
    for k in range(len(qs) - 1):
        if p_lo[k] == p_hi[k] and p_lo[k + 1] == p_hi[k + 1] and p_lo[k] == p_lo[k + 1]:
            ax.plot(
                [qs[k], qs[k + 1]],
                [p_lo[k], p_lo[k + 1]],
                color="#1f77b4",
                linewidth=3.5,
                solid_capstyle="round",
            )
        elif p_hi[k] - p_lo[k] > 0.01 or p_hi[k + 1] - p_lo[k + 1] > 0.01:
            ax.fill_between(
                [qs[k], qs[k + 1]],
                [p_lo[k], p_lo[k + 1]],
                [p_hi[k], p_hi[k + 1]],
                color="#1f77b4",
                alpha=0.25,
            )

    ps, q_lo, q_hi = sample_br2_curve(M)
    for k in range(len(ps) - 1):
        if q_lo[k] == q_hi[k] and q_lo[k + 1] == q_hi[k + 1] and q_lo[k] == q_lo[k + 1]:
            ax.plot(
                [q_lo[k], q_lo[k + 1]],
                [ps[k], ps[k + 1]],
                color="#d62728",
                linewidth=3.5,
                solid_capstyle="round",
            )
        elif q_hi[k] - q_lo[k] > 0.01 or q_hi[k + 1] - q_lo[k + 1] > 0.01:
            ax.fill_betweenx(
                [ps[k], ps[k + 1]],
                [q_lo[k], q_lo[k + 1]],
                [q_hi[k], q_hi[k + 1]],
                color="#d62728",
                alpha=0.25,
            )

    mix = mixed_equilibrium_interior(M)
    if mix is not None:
        p_star, q_star = mix
        ax.scatter([q_star], [p_star], s=140, c="black", zorder=5, marker="o")
        # Etiqueta hacia la esquina mas cercana del borde del cuadrado para no tapar las BR.
        mx = 22.0 if q_star <= 0.5 else -82.0
        my = 18.0 if p_star <= 0.5 else -42.0
        ax.annotate(
            f"Mixto\n(p*, q*)=({p_star:.3f}, {q_star:.3f})",
            xy=(q_star, p_star),
            xytext=(mx, my),
            textcoords="offset points",
            fontsize=12,
            color="black",
            bbox=_NASH_ANN_BBOX,
            arrowprops=_ARROW_NASH_MIXTO,
            annotation_clip=False,
            zorder=20,
        )

    for (i, j) in pure_nash_equilibria(M):
        p_pt = 1.0 if i == 0 else 0.0
        q_pt = 1.0 if j == 0 else 0.0
        ax.scatter(
            [q_pt],
            [p_pt],
            s=120,
            facecolors="none",
            edgecolors="green",
            linewidths=2.5,
            zorder=6,
        )
        (ox, oy), ha_a, va_a = _PURE_NASH_LABEL_STYLE.get(
            (float(q_pt), float(p_pt)),
            ((40.0, 44.0), "left", "bottom"),
        )
        ax.annotate(
            f"Nash puro\n({LABEL_ROW[i][:1]}, {LABEL_COL[j][:1]})",
            xy=(q_pt, p_pt),
            xytext=(ox, oy),
            textcoords="offset points",
            ha=ha_a,
            va=va_a,
            fontsize=12,
            color="green",
            bbox=_NASH_ANN_BBOX_PURO,
            arrowprops=_ARROW_NASH_PURO,
            annotation_clip=False,
            zorder=20,
        )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fs_ax = (11, 11, 10) if compact else (14, 14, 13)
    ax.set_xlabel(r"$q$ = prob. jugador 2 juega L", fontsize=fs_ax[0])
    ax.set_ylabel(r"$p$ = prob. jugador 1 juega A", fontsize=fs_ax[1])
    ax.set_title(
        "Interseccion de correspondencias de mejor respuesta en (q, p)",
        fontsize=13 if compact else 17,
        pad=10 if compact else 14,
    )
    ax.tick_params(axis="both", labelsize=fs_ax[2])
    ax.grid(True, alpha=0.3)

    if q_cursor is not None and p_cursor is not None:
        qc = float(np.clip(q_cursor, 0.0, 1.0))
        pc = float(np.clip(p_cursor, 0.0, 1.0))
        ax.axvline(qc, color="#7b1fa2", lw=2.2, ls=":", alpha=0.9, zorder=14)
        ax.axhline(pc, color="#7b1fa2", lw=2.2, ls=":", alpha=0.9, zorder=14)
        ax.scatter(
            [qc],
            [pc],
            s=220,
            c="#ffc107",
            zorder=17,
            marker="*",
            edgecolors="#4a148c",
            linewidths=1.6,
        )

    legend_elems = [
        Line2D([0], [0], color="#1f77b4", lw=3.5, label="BR1(q): mejor p ante q"),
        Line2D([0], [0], color="#d62728", lw=3.5, label="BR2(p): mejor q ante p"),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="black",
            markersize=14,
            label="Equilibrio mixto (si existe)",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markeredgecolor="green",
            markerfacecolor="none",
            markersize=14,
            label="Equilibrios puros",
        ),
    ]
    if q_cursor is not None and p_cursor is not None:
        legend_elems.append(
            Line2D(
                [0],
                [0],
                marker="*",
                color="w",
                markerfacecolor="#ffc107",
                markeredgecolor="#4a148c",
                markersize=14,
                label="Su posicion (q, p) con los deslizadores",
            )
        )
    ax.legend(
        handles=legend_elems,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.30),
        ncol=2,
        fontsize=9 if compact else 14,
        frameon=True,
        framealpha=0.96,
    )
    # Margen inferior amplio: la leyenda queda bajo el eje x y no se superpone al titulo horizontal (xlabel).
    fig.subplots_adjust(
        left=0.14 if compact else 0.12,
        right=0.98,
        top=0.84 if compact else 0.87,
        bottom=0.50 if compact else 0.48,
    )
    return fig


def _q_indiferencia_j1(M: PayoffMatrix) -> Optional[float]:
    """q en (0,1) donde EU1(A,q)=EU1(B,q), si existe y es unico."""
    den = (M.u1_AL - M.u1_AR) - (M.u1_BL - M.u1_BR)
    if abs(den) < 1e-12:
        return None
    q = (M.u1_BR - M.u1_AR) / den
    if 0.0 < q < 1.0:
        return float(q)
    return None


def _p_indiferencia_j2(M: PayoffMatrix) -> Optional[float]:
    """p en (0,1) donde EU2(L,p)=EU2(R,p), si existe."""
    den = (M.u2_AL - M.u2_AR) - (M.u2_BL - M.u2_BR)
    if abs(den) < 1e-12:
        return None
    p = (M.u2_BR - M.u2_BL) / den
    if 0.0 < p < 1.0:
        return float(p)
    return None


def plot_eu_jugador1_vs_q(
    M: PayoffMatrix, q_mark: Optional[float] = None, *, compact: bool = False
) -> plt.Figure:
    """EU del jugador 1 al variar q (prob. de L del jugador 2); BR1 donde cada curva domina.
    q_mark: probabilidad q actual (deslizador) para marcar en el eje horizontal."""
    q = np.linspace(0.0, 1.0, 400)
    eu_a = q * M.u1_AL + (1.0 - q) * M.u1_AR
    eu_b = q * M.u1_BL + (1.0 - q) * M.u1_BR

    fig, ax = plt.subplots(figsize=(6.8, 4.9) if compact else (11.0, 7.0))
    ax.plot(q, eu_a, color="#1f77b4", lw=3.0, label=r"$EU_1(A,q)=q\,u_1(A,L)+(1-q)\,u_1(A,R)$")
    ax.plot(q, eu_b, color="#ff7f0e", lw=3.0, label=r"$EU_1(B,q)=q\,u_1(B,L)+(1-q)\,u_1(B,R)$")
    ax.fill_between(
        q,
        eu_a,
        eu_b,
        where=(eu_a >= eu_b),
        alpha=0.22,
        color="#1f77b4",
        interpolate=True,
        label=r"Mejor respuesta: $A$ ($p=1$)",
    )
    ax.fill_between(
        q,
        eu_a,
        eu_b,
        where=(eu_a < eu_b),
        alpha=0.22,
        color="#ff7f0e",
        interpolate=True,
        label=r"Mejor respuesta: $B$ ($p=0$)",
    )

    q_ind = _q_indiferencia_j1(M)
    if q_ind is not None:
        ax.axvline(q_ind, color="0.35", ls="--", lw=1.2, alpha=0.85)
        y1 = max(float(np.max(eu_a)), float(np.max(eu_b)))
        ax.annotate(
            rf"$q$ indiferencia $\approx {q_ind:.3f}$",
            xy=(q_ind, y1),
            xytext=(10, -18),
            textcoords="offset points",
            fontsize=13 if compact else 20,
        )

    ax.set_xlim(0, 1)
    if q_mark is not None:
        qm = float(np.clip(q_mark, 0.0, 1.0))
        eu_a_m = qm * M.u1_AL + (1.0 - qm) * M.u1_AR
        eu_b_m = qm * M.u1_BL + (1.0 - qm) * M.u1_BR
        ax.axvline(qm, color="#7b1fa2", lw=3.0, zorder=10, alpha=0.95)
        ax.scatter([qm], [eu_a_m], s=160, c="#ffc107", zorder=11, edgecolors="#4a148c", linewidths=2)
        ax.scatter([qm], [eu_b_m], s=160, c="#ffc107", zorder=11, edgecolors="#4a148c", linewidths=2)
    ax.set_xlabel(
        r"$q$ = probabilidad de que el jugador 2 juegue $L$",
        fontsize=13 if compact else 22,
    )
    ax.set_ylabel(r"Utilidad esperada del jugador 1", fontsize=13 if compact else 22)
    ax.set_title(
        "Jugador 1: EU al mover la mezcla del jugador 2\ny region de mejor respuesta",
        fontsize=15 if compact else 24,
        pad=10 if compact else 18,
    )
    ax.tick_params(axis="both", labelsize=12 if compact else 20)
    ax.grid(True, alpha=0.3)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.26),
        ncol=2,
        fontsize=11 if compact else 18,
        frameon=True,
        framealpha=0.96,
    )
    fig.subplots_adjust(bottom=0.38, top=0.84)
    return fig


def plot_eu_jugador2_vs_p(
    M: PayoffMatrix, p_mark: Optional[float] = None, *, compact: bool = False
) -> plt.Figure:
    """EU del jugador 2 al variar p (prob. de A del jugador 1); BR2 donde cada curva domina.
    p_mark: probabilidad p actual (deslizador) para marcar en el eje horizontal."""
    p = np.linspace(0.0, 1.0, 400)
    eu_l = p * M.u2_AL + (1.0 - p) * M.u2_BL
    eu_r = p * M.u2_AR + (1.0 - p) * M.u2_BR

    fig, ax = plt.subplots(figsize=(6.8, 4.9) if compact else (11.0, 7.0))
    ax.plot(p, eu_l, color="#2ca02c", lw=3.0, label=r"$EU_2(L,p)=p\,u_2(A,L)+(1-p)\,u_2(B,L)$")
    ax.plot(p, eu_r, color="#d62728", lw=3.0, label=r"$EU_2(R,p)=p\,u_2(A,R)+(1-p)\,u_2(B,R)$")
    ax.fill_between(
        p,
        eu_l,
        eu_r,
        where=(eu_l >= eu_r),
        alpha=0.22,
        color="#2ca02c",
        interpolate=True,
        label=r"Mejor respuesta: $L$ ($q=1$)",
    )
    ax.fill_between(
        p,
        eu_l,
        eu_r,
        where=(eu_l < eu_r),
        alpha=0.22,
        color="#d62728",
        interpolate=True,
        label=r"Mejor respuesta: $R$ ($q=0$)",
    )

    p_ind = _p_indiferencia_j2(M)
    if p_ind is not None:
        ax.axvline(p_ind, color="0.35", ls="--", lw=1.2, alpha=0.85)
        y1 = max(float(np.max(eu_l)), float(np.max(eu_r)))
        ax.annotate(
            rf"$p$ indiferencia $\approx {p_ind:.3f}$",
            xy=(p_ind, y1),
            xytext=(10, -18),
            textcoords="offset points",
            fontsize=13 if compact else 20,
        )

    ax.set_xlim(0, 1)
    if p_mark is not None:
        pm = float(np.clip(p_mark, 0.0, 1.0))
        eu_l_m = pm * M.u2_AL + (1.0 - pm) * M.u2_BL
        eu_r_m = pm * M.u2_AR + (1.0 - pm) * M.u2_BR
        ax.axvline(pm, color="#7b1fa2", lw=3.0, zorder=10, alpha=0.95)
        ax.scatter([pm], [eu_l_m], s=160, c="#ffc107", zorder=11, edgecolors="#4a148c", linewidths=2)
        ax.scatter([pm], [eu_r_m], s=160, c="#ffc107", zorder=11, edgecolors="#4a148c", linewidths=2)
    ax.set_xlabel(
        r"$p$ = probabilidad de que el jugador 1 juegue $A$",
        fontsize=13 if compact else 22,
    )
    ax.set_ylabel(r"Utilidad esperada del jugador 2", fontsize=13 if compact else 22)
    ax.set_title(
        "Jugador 2: EU al mover la mezcla del jugador 1\ny region de mejor respuesta",
        fontsize=15 if compact else 24,
        pad=10 if compact else 18,
    )
    ax.tick_params(axis="both", labelsize=12 if compact else 20)
    ax.grid(True, alpha=0.3)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.26),
        ncol=2,
        fontsize=11 if compact else 18,
        frameon=True,
        framealpha=0.96,
    )
    fig.subplots_adjust(bottom=0.38, top=0.84)
    return fig


_BIMATRIX_CSS = """
<style>
.bimatrix-wrap { max-width: 100%; margin: 0 0 0.35rem 0; }
.bimatrix-j2 { text-align: center; font-weight: 700; font-size: 1.08rem; margin: 0.05rem 0 0.2rem 0; letter-spacing: 0.02em; }
.bimatrix-colhead { text-align: center; font-weight: 600; font-size: 1rem; margin-bottom: 0.2rem; color: #1a1a1a; }
.bimatrix-j1-rows {
  display: flex;
  min-height: 168px;
  align-items: stretch;
  padding: 0.08rem 0.2rem 0.08rem 0;
}
.bimatrix-j1-rows .j1-rot {
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  color: #1a1a1a;
  padding: 0 0.35rem 0 0;
  white-space: nowrap;
}
.bimatrix-j1-rows .j1-rows {
  display: flex;
  flex-direction: column;
  flex: 1;
  justify-content: space-between;
  padding: 0.5rem 0 0.5rem 0.2rem;
}
.bimatrix-j1-rows .j1-rows div {
  text-align: center;
  font-weight: 700;
  font-size: 1rem;
  color: #1a1a1a;
}
.bimatrix-comma { text-align: center; font-weight: 600; padding-top: 0.85rem; font-size: 1.15rem; color: #333; }
.bimatrix-sp-spacer { height: 0; margin: 0; padding: 0; line-height: 0; font-size: 0; width: 0; overflow: hidden; }
</style>
"""

_J1_ROWS_HTML = """
<div class="bimatrix-j1-rows">
  <div class="j1-rot">J₁</div>
  <div class="j1-rows">
    <div>A</div>
    <div>B</div>
  </div>
</div>
"""


def _payoff_cell_pair(u1_key: str, u2_key: str) -> None:
    """Una celda con dos entradas (pago J₁, pago J₂), formato convencional u₁, u₂."""
    c1, cm, c2 = st.columns([2.2, 0.45, 2.2], gap="small")
    with c1:
        st.number_input("u1", key=u1_key, label_visibility="collapsed", step=0.01, format="%.4g")
    with cm:
        st.markdown('<p class="bimatrix-comma">,</p>', unsafe_allow_html=True)
    with c2:
        st.number_input("u2", key=u2_key, label_visibility="collapsed", step=0.01, format="%.4g")


def render_conventional_bimatrix() -> None:
    """Matriz normal 2x2: J₁ a la izquierda, J₂ arriba, celdas (u₁, u₂) editables."""
    st.markdown(_BIMATRIX_CSS, unsafe_allow_html=True)
    st.markdown('<div class="bimatrix-wrap">', unsafe_allow_html=True)

    sp, top = st.columns([0.18, 0.82])
    with sp:
        st.markdown(
            '<div class="bimatrix-sp-spacer" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
    with top:
        st.markdown('<p class="bimatrix-j2">J₂</p>', unsafe_allow_html=True)
        hL, hR = st.columns(2)
        with hL:
            st.markdown('<p class="bimatrix-colhead">L</p>', unsafe_allow_html=True)
        with hR:
            st.markdown('<p class="bimatrix-colhead">R</p>', unsafe_allow_html=True)

    j1lab, cL, cR = st.columns([0.18, 0.41, 0.41])
    with j1lab:
        st.markdown(_J1_ROWS_HTML, unsafe_allow_html=True)
    with cL:
        with st.container(border=True):
            _payoff_cell_pair("u1al", "u2al")
        with st.container(border=True):
            _payoff_cell_pair("u1bl", "u2bl")
    with cR:
        with st.container(border=True):
            _payoff_cell_pair("u1ar", "u2ar")
        with st.container(border=True):
            _payoff_cell_pair("u1br", "u2br")

    st.markdown("</div>", unsafe_allow_html=True)


st.markdown(
    """
<style>
.block-container { padding-top: 1.1rem; }
h1.fnj-app-title {
  font-size: clamp(1.15rem, 4vw, 2rem) !important;
  text-align: center;
}
div[data-testid="stExpander"] summary { font-weight: 600; }
/*
 * Los <div class="payoff-card"> en markdown NO envuelven st.number_input en el DOM (Streamlit
 * apila bloques hermanos). Para subir la matriz hace falta afectar la columna real o usar transform.
 */
div[data-testid="column"]:has(p.fnj-section-title) {
  transform: translateY(-2.1rem);
}
div[data-testid="column"]:has(p.fnj-section-title) div[data-testid="stVerticalBlock"] {
  gap: 0.15rem !important;
}
p.fnj-section-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0.1rem 0 0.35rem 0;
  line-height: 1.2;
  color: #262730;
}
div[data-testid="stMetricValue"] { font-size: 1.05rem !important; }
div[data-testid="stMetricLabel"] { font-size: 0.85rem !important; }
p.exploracion-br {
  font-size: 0.98rem;
  font-weight: 600;
  margin: 0.15rem 0 0.4rem 0;
  line-height: 1.25;
  color: #262730;
}
p.eu-one-line {
  white-space: nowrap;
  overflow-x: auto;
  font-size: 1rem;
  margin: 0.12rem 0 0.35rem 0;
  line-height: 1.35;
  color: #262730;
}
p.br-qp-title {
  font-size: clamp(0.8rem, 2.8vw, 1.12rem);
  font-weight: 600;
  margin: -0.45rem 0 0.12rem 0;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #1a1a1a;
}
/* Menos hueco entre matriz y titulo del grafico (q,p) */
div.br-qp-gap-tight {
  height: 0;
  margin-top: -0.85rem;
  margin-bottom: 0;
  line-height: 0;
  font-size: 0;
}
/* Acerca la figura (q,p) al titulo sin envolver st.pyplot en HTML */
div.br-qp-fig-spacer {
  height: 0;
  margin-top: -0.65rem;
  margin-bottom: 0;
  line-height: 0;
  font-size: 0;
}
/* Sube el contenido de la columna derecha (exploracion + graficas) en la pestana interactiva */
div.col-plots-pull-spacer {
  height: 0;
  margin-top: -1.2rem;
  margin-bottom: 0;
  line-height: 0;
  font-size: 0;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div style="text-align: center; margin-bottom: 1rem;">
<h1 class="fnj-app-title" style="font-weight: 700; margin: 0 0 0.45rem 0; line-height: 1.2;">
Análisis Equilibrio de Nash (2x2)
</h1>
<p style="font-size: 1.05rem; margin: 0.25rem 0; line-height: 1.35;">Pr. Humberto Bernal</p>
<p style="font-size: 0.98rem; margin: 0.25rem 0; line-height: 1.35;">
<a href="mailto:hbernal@universidadmayor.edu.co">hbernal@universidadmayor.edu.co</a>
</p>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """
Jugador 1 elige **fila** ($A$ o $B$), jugador 2 elige **columna** ($L$ o $R$).
En cada celda el par **(pago de J₁, pago de J₂)** sigue la convencion habitual (fila, columna). Edite los valores en la matriz y revise el resumen de equilibrios.
"""
)

tab_matriz, tab_teoria = st.tabs(["Matriz e interaccion", "Teoria y derivacion"])

with tab_matriz:
    if _MOBILE_UI:
        col_controls = st.container()
        col_plots = st.container()
    else:
        col_controls, col_plots = st.columns([0.36, 0.64], gap="large")

    with col_controls:
        st.markdown(
            '<p class="fnj-section-title">Forma Normal del Juego</p>',
            unsafe_allow_html=True,
        )
        render_conventional_bimatrix()
        st.markdown('<div class="br-qp-gap-tight"></div>', unsafe_allow_html=True)

        M = PayoffMatrix(
            st.session_state["u1al"],
            st.session_state["u1ar"],
            st.session_state["u1bl"],
            st.session_state["u1br"],
            st.session_state["u2al"],
            st.session_state["u2ar"],
            st.session_state["u2bl"],
            st.session_state["u2br"],
        )

        pures = pure_nash_equilibria(M)
        mix = mixed_equilibrium_interior(M)

        st.markdown(
            '<p class="br-qp-title" title="Grafico (q, p): interseccion de correspondencias">'
            "Grafico (q, p): interseccion de correspondencias</p>",
            unsafe_allow_html=True,
        )
        q_br = float(st.session_state.get("qs_expl", 0.5))
        p_br = float(st.session_state.get("ps", 0.5))
        fig_br = plot_best_response(M, q_cursor=q_br, p_cursor=p_br, compact=_MOBILE_UI)
        st.markdown('<div class="br-qp-fig-spacer"></div>', unsafe_allow_html=True)
        st.pyplot(fig_br, use_container_width=True)
        plt.close(fig_br)

    with col_plots:
        if not _MOBILE_UI:
            st.markdown('<div class="col-plots-pull-spacer"></div>', unsafe_allow_html=True)
        if _MOBILE_UI:
            q_slider = st.slider(
                r"Probabilidad $q$ de que el jugador 2 juegue $L$",
                0.0,
                1.0,
                0.5,
                0.01,
                key="qs_expl",
            )
            eu_a = expected_u1_A(q_slider, M)
            eu_b = expected_u1_B(q_slider, M)
            p_lo, p_hi = br1_correspondence(q_slider, M)
            p_slider = st.slider(
                r"Probabilidad $p$ de que el jugador 1 juegue $A$",
                0.0,
                1.0,
                0.5,
                0.01,
                key="ps",
            )
            ev_l = expected_u2_L(p_slider, M)
            ev_r = expected_u2_R(p_slider, M)
            q_lo, q_hi = br2_correspondence(p_slider, M)
        else:
            row_sl_q, row_sl_p = st.columns(2, gap="medium")
            with row_sl_q:
                q_slider = st.slider(
                    r"Probabilidad $q$ de que el jugador 2 juegue $L$",
                    0.0,
                    1.0,
                    0.5,
                    0.01,
                    key="qs_expl",
                )
                eu_a = expected_u1_A(q_slider, M)
                eu_b = expected_u1_B(q_slider, M)
                p_lo, p_hi = br1_correspondence(q_slider, M)
            with row_sl_p:
                p_slider = st.slider(
                    r"Probabilidad $p$ de que el jugador 1 juegue $A$",
                    0.0,
                    1.0,
                    0.5,
                    0.01,
                    key="ps",
                )
                ev_l = expected_u2_L(p_slider, M)
                ev_r = expected_u2_R(p_slider, M)
                q_lo, q_hi = br2_correspondence(p_slider, M)

        if _MOBILE_UI:
            _bm1, _bm2 = st.container(), st.container()
        else:
            _bm1, _bm2 = st.columns(2, gap="medium")
        with _bm1:
            if p_lo == p_hi:
                accion = "A" if p_lo >= 0.999 else "B"
                st.success(
                    f"Mejor respuesta del jugador 1: **jugar {accion}** (estrategia pura, $p={p_lo:.0f}$)."
                )
            else:
                st.info("Indiferencia: **cualquier** $p\\in[0,1]$ es mejor respuesta del jugador 1.")
        with _bm2:
            if q_lo == q_hi:
                accion2 = "L" if q_lo >= 0.999 else "R"
                st.success(
                    f"Mejor respuesta del jugador 2: **jugar {accion2}** (estrategia pura, $q={q_lo:.0f}$)."
                )
            else:
                st.info("Indiferencia: **cualquier** $q\\in[0,1]$ es mejor respuesta del jugador 2.")

        if _MOBILE_UI:
            _cq, _cp = st.container(), st.container()
        else:
            _cq, _cp = st.columns(2, gap="medium")
        with _cq:
            st.markdown(
                '<p class="exploracion-br">Exploracion: fije q y vea la mejor respuesta de 1</p>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<p class="eu-one-line">E[u<sub>1</sub>|A] = {eu_a:.3f} &nbsp;·&nbsp; '
                f"E[u<sub>1</sub>|B] = {eu_b:.3f}</p>",
                unsafe_allow_html=True,
            )
        with _cp:
            st.markdown(
                '<p class="exploracion-br">Exploracion: fije p y vea la mejor respuesta de 2</p>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<p class="eu-one-line">E[u<sub>2</sub>|L] = {ev_l:.3f} &nbsp;·&nbsp; '
                f"E[u<sub>2</sub>|R] = {ev_r:.3f}</p>",
                unsafe_allow_html=True,
            )

        if _MOBILE_UI:
            _g1, _g2 = st.container(), st.container()
        else:
            _g1, _g2 = st.columns(2, gap="small")
        with _g1:
            fig1 = plot_eu_jugador1_vs_q(M, q_mark=q_slider, compact=_MOBILE_UI)
            st.pyplot(fig1, use_container_width=True)
            plt.close(fig1)
        with _g2:
            fig2 = plot_eu_jugador2_vs_p(M, p_mark=p_slider, compact=_MOBILE_UI)
            st.pyplot(fig2, use_container_width=True)
            plt.close(fig2)

        st.subheader("Resultado: equilibrios de Nash")
        if _MOBILE_UI:
            m1, m2 = st.container(), st.container()
        else:
            m1, m2 = st.columns(2)
        with m1:
            st.metric("Cantidad de Nash puros", str(len(pures)))
        with m2:
            if mix is not None:
                p_star, q_star = mix
                st.metric(
                    "Nash mixto interior",
                    f"p* = {p_star:.3f},  q* = {q_star:.3f}",
                    help="p*: prob. de A (jug. 1); q*: prob. de L (jug. 2)",
                )
            else:
                st.metric("Nash mixto interior", "No aplica (0 < p,q < 1)")

        res_lines = []
        if pures:
            for (i, j) in pures:
                res_lines.append(
                    f"- **({LABEL_ROW[i][0]}, {LABEL_COL[j][0]})** — "
                    f"pagos $(u_1,u_2)=({M.u1_row(i, j):.4g}, {M.u2_row(i, j):.4g})$."
                )
            st.success("**Nash puros:**\n\n" + "\n".join(res_lines))
        else:
            st.warning("No hay equilibrio de Nash en estrategias puras para estos pagos.")

        if mix is not None:
            p_star, q_star = mix
            st.info(
                f"**Nash mixto interior:** aproximadamente $(p^*, q^*) = ({p_star:.3f}, {q_star:.3f})$ "
                r"(el jugador 1 mezcla $A$ con probabilidad $p^*$ y el jugador 2 mezcla $L$ con $q^*$)."
            )
        else:
            st.caption(
                "No hay equilibrio completamente mixto con $0<p,q<1$, o las condiciones de indiferencia no definen un unico punto interior."
            )

        st.subheader("Graficas: utilidad esperada y mejor respuesta")
        st.markdown(
            r"""
**Jugador 1:** en el eje horizontal se mueve $q$, la probabilidad de que el jugador 2 juegue $L$.
Las curvas son $EU_1(A,q)$ y $EU_1(B,q)$. Donde una curva está por encima de la otra, la **mejor respuesta**
del jugador 1 es la fila correspondiente (mezcla pura $p=1$ para $A$ o $p=0$ para $B$). Si se cortan en
$(0,1)$, en ese $q$ el jugador 1 es **indiferente** entre $A$ y $B$ (cualquier $p$ es mejor respuesta).

**Jugador 2:** en el eje horizontal se mueve $p$, la probabilidad de que el jugador 1 juegue $A$.
Las curvas son $EU_2(L,p)$ y $EU_2(R,p)$; la region sombreada indica la mejor respuesta en columnas ($q=1$
para $L$ o $q=0$ para $R$), salvo indiferencia en el cruce interior.
"""
        )


with tab_teoria:
    st.subheader("1. Mejor respuesta en estrategias puras")
    st.markdown(
        r"""
Si el jugador 2 juega $L$, el jugador 1 compara $u_1(A,L)$ con $u_1(B,L)$ y elige la fila con mayor pago.
Si el jugador 2 juega $R$, compara $u_1(A,R)$ con $u_1(B,R)$.

**Correspondencia de mejor respuesta del jugador 1**: conjunto de filas optimas ante cada columna (o mezcla) del rival.

Analogamente, el jugador 2 compara $u_2(\cdot,L)$ y $u_2(\cdot,R)$ **fijando la fila** del jugador 1.
"""
    )
    st.subheader("2. Mejor respuesta ante mezclas del rival")
    st.markdown(
        r"""
Suponga que el jugador 2 juega $L$ con probabilidad $q\in[0,1]$ y $R$ con $1-q$.
Los pagos esperados del jugador 1 si el juega $A$ o $B$ son:

$$
\mathbb{E}[u_1\mid A] = q\,u_1(A,L) + (1-q)\,u_1(A,R),\qquad
\mathbb{E}[u_1\mid B] = q\,u_1(B,L) + (1-q)\,u_1(B,R).
$$

La **mejor respuesta** del jugador 1 en probabilidades $p$ de jugar $A$ maximiza su pago esperado dado $q$.
- Si $\mathbb{E}[u_1\mid A]>\mathbb{E}[u_1\mid B]$, la unica mejor respuesta pura es $A$ ($p=1$).
- Si la desigualdad es estricta al reves, la mejor respuesta es $B$ ($p=0$).
- Si hay **indiferencia**, cualquier $p$ es mejor respuesta (segmento vertical en el grafico $(q,p)$).

El jugador 2, si el jugador 1 mezcla con probabilidad $p$ de $A$, tiene:

$$
\mathbb{E}[u_2\mid L] = p\,u_2(A,L) + (1-p)\,u_2(B,L),\qquad
\mathbb{E}[u_2\mid R] = p\,u_2(A,R) + (1-p)\,u_2(B,R).
$$

La mejor respuesta en $q$ es analoga; en el plano $(q,p)$ aparece como **segmento horizontal** cuando hay indiferencia.
"""
    )
    st.subheader("3. Equilibrio de Nash")
    st.markdown(
        r"""
Un **perfil** $(p,q)$ es equilibrio de Nash si $p$ es mejor respuesta a $q$ **y** $q$ es mejor respuesta a $p$.
En el grafico, son los **puntos de interseccion** de las dos correspondencias (y los segmentos donde coinciden).

- **Equilibrios puros**: esquinas $(0,0),(0,1),(1,0),(1,1)$ que satisfacen ambas mejor respuesta.
- **Equilibrio mixto interior**: cuando ambas indiferencias ocurren con $0<p,q<1$, se resuelve el sistema lineal que iguala los pagos esperados entre las dos acciones de cada jugador.
"""
    )


st.caption("Carpeta `teoria_de_juegos_web`: ejecute `python3 -m streamlit run streamlit_app.py` desde esa carpeta.")
