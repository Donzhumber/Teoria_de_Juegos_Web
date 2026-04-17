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
    page_title="Nash 2x2 - Mejor respuesta",
    page_icon="",
    layout="wide",
)

LABEL_ROW = ("A (fila arriba)", "B (fila abajo)")
LABEL_COL = ("L (col. izq.)", "R (col. der.)")

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

with st.sidebar:
    st.header("Ejemplos")
    preset_name = st.selectbox("Matriz de ejemplo", list(PRESETS.keys()))
    if st.button("Cargar ejemplo seleccionado"):
        for k, v in zip(_KEYS, PRESETS[preset_name]):
            st.session_state[k] = v
        st.rerun()


def plot_best_response(M: PayoffMatrix) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7.2, 6.2))

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
        ax.annotate(
            f"Mixto\n(p*, q*)=({p_star:.3f}, {q_star:.3f})",
            xy=(q_star, p_star),
            xytext=(10, 12),
            textcoords="offset points",
            fontsize=10,
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
        ax.annotate(
            f"Nash puro\n({LABEL_ROW[i][:1]}, {LABEL_COL[j][:1]})",
            xy=(q_pt, p_pt),
            xytext=(-18, -22),
            textcoords="offset points",
            fontsize=9,
            color="green",
        )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel(r"$q$ = prob. jugador 2 juega L", fontsize=12)
    ax.set_ylabel(r"$p$ = prob. jugador 1 juega A", fontsize=12)
    ax.set_title("Interseccion de correspondencias de mejor respuesta en (q, p)", fontsize=13)
    ax.grid(True, alpha=0.3)

    legend_elems = [
        Line2D([0], [0], color="#1f77b4", lw=3.5, label="BR1(q): mejor p ante q"),
        Line2D([0], [0], color="#d62728", lw=3.5, label="BR2(p): mejor q ante p"),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor="black",
            markersize=9,
            label="Equilibrio mixto (si existe)",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markeredgecolor="green",
            markerfacecolor="none",
            markersize=9,
            label="Equilibrios puros",
        ),
    ]
    ax.legend(handles=legend_elems, loc="upper left", fontsize=9)
    fig.tight_layout()
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


def plot_eu_jugador1_vs_q(M: PayoffMatrix) -> plt.Figure:
    """EU del jugador 1 al variar q (prob. de L del jugador 2); BR1 donde cada curva domina."""
    q = np.linspace(0.0, 1.0, 400)
    eu_a = q * M.u1_AL + (1.0 - q) * M.u1_AR
    eu_b = q * M.u1_BL + (1.0 - q) * M.u1_BR

    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.plot(q, eu_a, color="#1f77b4", lw=2.4, label=r"$EU_1(A,q)=q\,u_1(A,L)+(1-q)\,u_1(A,R)$")
    ax.plot(q, eu_b, color="#ff7f0e", lw=2.4, label=r"$EU_1(B,q)=q\,u_1(B,L)+(1-q)\,u_1(B,R)$")
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
            xytext=(8, -12),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_xlim(0, 1)
    ax.set_xlabel(r"$q$ = probabilidad de que el jugador 2 juegue $L$", fontsize=11)
    ax.set_ylabel(r"Utilidad esperada del jugador 1", fontsize=11)
    ax.set_title("Jugador 1: EU al mover la mezcla del jugador 2 y region de mejor respuesta", fontsize=12)
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_eu_jugador2_vs_p(M: PayoffMatrix) -> plt.Figure:
    """EU del jugador 2 al variar p (prob. de A del jugador 1); BR2 donde cada curva domina."""
    p = np.linspace(0.0, 1.0, 400)
    eu_l = p * M.u2_AL + (1.0 - p) * M.u2_BL
    eu_r = p * M.u2_AR + (1.0 - p) * M.u2_BR

    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.plot(p, eu_l, color="#2ca02c", lw=2.4, label=r"$EU_2(L,p)=p\,u_2(A,L)+(1-p)\,u_2(B,L)$")
    ax.plot(p, eu_r, color="#d62728", lw=2.4, label=r"$EU_2(R,p)=p\,u_2(A,R)+(1-p)\,u_2(B,R)$")
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
            xytext=(8, -12),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_xlim(0, 1)
    ax.set_xlabel(r"$p$ = probabilidad de que el jugador 1 juegue $A$", fontsize=11)
    ax.set_ylabel(r"Utilidad esperada del jugador 2", fontsize=11)
    ax.set_title("Jugador 2: EU al mover la mezcla del jugador 1 y region de mejor respuesta", fontsize=12)
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def _fmt_pago(x: float) -> str:
    return f"{x:g}"


def payoff_matrices_markdown(M: PayoffMatrix) -> str:
    """Tablas Markdown: bimatriz y una matriz por jugador."""
    a11 = _fmt_pago(M.u1_AL)
    a12 = _fmt_pago(M.u1_AR)
    a21 = _fmt_pago(M.u1_BL)
    a22 = _fmt_pago(M.u1_BR)
    b11 = _fmt_pago(M.u2_AL)
    b12 = _fmt_pago(M.u2_AR)
    b21 = _fmt_pago(M.u2_BL)
    b22 = _fmt_pago(M.u2_BR)
    return f"""
**Forma bimatricial** (cada celda: pago del jugador 1, pago del jugador 2). El jugador 1 elige **fila** ($A$ arriba, $B$ abajo); el jugador 2 elige **columna** ($L$ izquierda, $R$ derecha).

|  | $L$ | $R$ |
|:--|:--|:--|
| **$A$** | ({a11}, {b11}) | ({a12}, {b12}) |
| **$B$** | ({a21}, {b21}) | ({a22}, {b22}) |

**Solo jugador 1** ($u_1$; filas $A,B$; columnas $L,R$):

|  | $L$ | $R$ |
|:--|:--|:--|
| **$A$** | {a11} | {a12} |
| **$B$** | {a21} | {a22} |

**Solo jugador 2** ($u_2$):

|  | $L$ | $R$ |
|:--|:--|:--|
| **$A$** | {b11} | {b12} |
| **$B$** | {b21} | {b22} |
"""


st.title("Del mejor respuesta al equilibrio de Nash (juego 2 por 2)")
st.markdown(
    """
Jugador 1 elige **fila** ($A$ o $B$), jugador 2 elige **columna** ($L$ o $R$).
Cada casilla tiene un par $(u_1, u_2)$.
"""
)

tab_teoria, tab_interactivo = st.tabs(["Teoria y derivacion", "Matriz e interaccion"])

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

with tab_interactivo:
    col_left, col_right = st.columns([1.05, 1.0])
    with col_left:
        st.subheader("Pagos de la matriz")
        st.caption("Edite los valores; la app recalcula equilibrios y el grafico.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{LABEL_COL[0]}**")
            u1_AL = st.number_input(r"$u_1(A,L)$", key="u1al")
            u2_AL = st.number_input(r"$u_2(A,L)$", key="u2al")
            u1_BL = st.number_input(r"$u_1(B,L)$", key="u1bl")
            u2_BL = st.number_input(r"$u_2(B,L)$", key="u2bl")
        with c2:
            st.markdown(f"**{LABEL_COL[1]}**")
            u1_AR = st.number_input(r"$u_1(A,R)$", key="u1ar")
            u2_AR = st.number_input(r"$u_2(A,R)$", key="u2ar")
            u1_BR = st.number_input(r"$u_1(B,R)$", key="u1br")
            u2_BR = st.number_input(r"$u_2(B,R)$", key="u2br")

    M = PayoffMatrix(u1_AL, u1_AR, u1_BL, u1_BR, u2_AL, u2_AR, u2_BL, u2_BR)

    with col_right:
        st.subheader("Exploracion: fije q y vea la mejor respuesta de 1")
        q_slider = st.slider(
            r"Probabilidad $q$ de que el jugador 2 juegue $L$",
            0.0,
            1.0,
            0.5,
            0.01,
        )
        eu_a = expected_u1_A(q_slider, M)
        eu_b = expected_u1_B(q_slider, M)
        p_lo, p_hi = br1_correspondence(q_slider, M)
        st.write(f"$\mathbb{{E}}[u_1\\mid A] = {eu_a:.4f}$")
        st.write(f"$\mathbb{{E}}[u_1\\mid B] = {eu_b:.4f}$")
        if p_lo == p_hi:
            accion = "A" if p_lo >= 0.999 else "B"
            st.success(
                f"Mejor respuesta del jugador 1: **jugar {accion}** (estrategia pura, $p={p_lo:.0f}$)."
            )
        else:
            st.info("Indiferencia: **cualquier** $p\\in[0,1]$ es mejor respuesta del jugador 1.")

        st.subheader("Exploracion: fije p y vea la mejor respuesta de 2")
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
        st.write(f"$\mathbb{{E}}[u_2\\mid L] = {ev_l:.4f}$")
        st.write(f"$\mathbb{{E}}[u_2\\mid R] = {ev_r:.4f}$")
        if q_lo == q_hi:
            accion2 = "L" if q_lo >= 0.999 else "R"
            st.success(
                f"Mejor respuesta del jugador 2: **jugar {accion2}** (estrategia pura, $q={q_lo:.0f}$)."
            )
        else:
            st.info("Indiferencia: **cualquier** $q\\in[0,1]$ es mejor respuesta del jugador 2.")

    st.subheader("Vista matricial de los pagos")
    st.markdown(
        "Las mismas entradas que en los campos de arriba, en forma de **matrices**: "
        "en cada celda, la **primera** cifra es el pago del jugador 1 (filas $A,B$) y la **segunda** "
        "la del jugador 2 (columnas $L,R$)."
    )
    st.markdown(payoff_matrices_markdown(M))

    st.subheader("Graficas: utilidad esperada y mejor respuesta")
    st.markdown(
        r"""
**Jugador 1:** en el eje horizontal se mueve $q$, la probabilidad de que el jugador 2 juegue $L$.
Las curvas son $EU_1(A,q)$ y $EU_1(B,q)$. Donde una curva est? por encima de la otra, la **mejor respuesta**
del jugador 1 es la fila correspondiente (mezcla pura $p=1$ para $A$ o $p=0$ para $B$). Si se cortan en
$(0,1)$, en ese $q$ el jugador 1 es **indiferente** entre $A$ y $B$ (cualquier $p$ es mejor respuesta).

**Jugador 2:** en el eje horizontal se mueve $p$, la probabilidad de que el jugador 1 juegue $A$.
Las curvas son $EU_2(L,p)$ y $EU_2(R,p)$; la region sombreada indica la mejor respuesta en columnas ($q=1$
para $L$ o $q=0$ para $R$), salvo indiferencia en el cruce interior.
"""
    )
    g1, g2 = st.columns(2)
    with g1:
        fig1 = plot_eu_jugador1_vs_q(M)
        st.pyplot(fig1)
        plt.close(fig1)
    with g2:
        fig2 = plot_eu_jugador2_vs_p(M)
        st.pyplot(fig2)
        plt.close(fig2)

    st.divider()
    st.subheader("Equilibrios encontrados")
    pures = pure_nash_equilibria(M)
    mix = mixed_equilibrium_interior(M)

    pc = st.columns(2)
    with pc[0]:
        st.markdown("**Nash puros** (celdas donde nadie gana desviandose solo):")
        if not pures:
            st.warning("Ningun equilibrio de Nash puro en esta matriz.")
        for (i, j) in pures:
            st.write(
                f"- Perfil **({LABEL_ROW[i][0]}, {LABEL_COL[j][0]})** "
                f"con pagos $(u_1,u_2)=({M.u1_row(i,j):.3g}, {M.u2_row(i,j):.3g})$."
            )
    with pc[1]:
        st.markdown("**Nash mixto interior** (si aplica):")
        if mix is None:
            st.write("No hay equilibrio completamente mixto con $0<p,q<1$ (o no esta bien definido).")
        else:
            p_star, q_star = mix
            st.write(
                rf"$(p^*,q^*) \approx ({p_star:.4f}, {q_star:.4f})$: "
                "jugador 1 mezcla $A$ con $p^*$ y el 2 mezcla $L$ con $q^*$."
            )

    st.subheader("Grafico (q, p): interseccion de correspondencias")
    fig = plot_best_response(M)
    st.pyplot(fig)
    plt.close(fig)

st.caption("Carpeta `teoria_de_juegos_web`: ejecute `python3 -m streamlit run streamlit_app.py` desde esa carpeta.")
