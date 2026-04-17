"""
Logica de juego 2x2: mejor respuesta y equilibrios de Nash (puros y mixtos).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class PayoffMatrix:
    """Jugador 1 elige fila (A arriba, B abajo), jugador 2 columna (L izq, R der)."""
    u1_AL: float
    u1_AR: float
    u1_BL: float
    u1_BR: float
    u2_AL: float
    u2_AR: float
    u2_BL: float
    u2_BR: float

    def u1_row(self, row: int, col: int) -> float:
        return (
            (self.u1_AL, self.u1_AR)[col] if row == 0 else (self.u1_BL, self.u1_BR)[col]
        )

    def u2_row(self, row: int, col: int) -> float:
        return (
            (self.u2_AL, self.u2_AR)[col] if row == 0 else (self.u2_BL, self.u2_BR)[col]
        )


def pure_nash_equilibria(M: PayoffMatrix) -> List[Tuple[int, int]]:
    """Devuelve lista de (fila, columna) en equilibrio de Nash puro."""
    out: List[Tuple[int, int]] = []
    for i in (0, 1):
        for j in (0, 1):
            br1 = M.u1_row(i, j) >= M.u1_row(1 - i, j)
            br2 = M.u2_row(i, j) >= M.u2_row(i, 1 - j)
            if br1 and br2:
                out.append((i, j))
    return out


def expected_u1_A(q: float, M: PayoffMatrix) -> float:
    return q * M.u1_AL + (1.0 - q) * M.u1_AR


def expected_u1_B(q: float, M: PayoffMatrix) -> float:
    return q * M.u1_BL + (1.0 - q) * M.u1_BR


def expected_u2_L(p: float, M: PayoffMatrix) -> float:
    return p * M.u2_AL + (1.0 - p) * M.u2_BL


def expected_u2_R(p: float, M: PayoffMatrix) -> float:
    return p * M.u2_AR + (1.0 - p) * M.u2_BR


def br1_correspondence(q: float, M: PayoffMatrix) -> Tuple[float, float]:
    """
    Conjunto de probabilidades p (jugar fila A) que son mejor respuesta a q.
    Devuelve (p_min, p_max) en [0,1]; si puro, p_min=p_max.
    """
    a = expected_u1_A(q, M)
    b = expected_u1_B(q, M)
    eps = 1e-9
    if a > b + eps:
        return (1.0, 1.0)
    if b > a + eps:
        return (0.0, 0.0)
    return (0.0, 1.0)


def br2_correspondence(p: float, M: PayoffMatrix) -> Tuple[float, float]:
    """Mejor respuesta en q (prob. columna L) ante p."""
    l = expected_u2_L(p, M)
    r = expected_u2_R(p, M)
    eps = 1e-9
    if l > r + eps:
        return (1.0, 1.0)
    if r > l + eps:
        return (0.0, 0.0)
    return (0.0, 1.0)


def mixed_equilibrium_interior(M: PayoffMatrix) -> Optional[Tuple[float, float]]:
    """
    Si existe equilibrio completamente mixto (0<p,q<1), devuelve (p*, q*).
    Caso contrario None.
    """
    # Indiferencia jugador 1: E[u1|A] = E[u1|B]
    num1 = M.u1_BR - M.u1_AR
    den1 = (M.u1_AL - M.u1_AR) - (M.u1_BL - M.u1_BR)
    if abs(den1) < 1e-12:
        q_star = None
    else:
        q_star = num1 / den1

    num2 = M.u2_BR - M.u2_BL
    den2 = (M.u2_AL - M.u2_BL) - (M.u2_AR - M.u2_BR)
    if abs(den2) < 1e-12:
        p_star = None
    else:
        p_star = num2 / den2

    if q_star is None or p_star is None:
        return None
    if not (0.0 < q_star < 1.0 and 0.0 < p_star < 1.0):
        return None
    return (float(p_star), float(q_star))


def sample_br1_curve(M: PayoffMatrix, n: int = 501) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Para cada q, p_min y p_max de BR1."""
    qs = np.linspace(0.0, 1.0, n)
    p_lo = np.empty(n)
    p_hi = np.empty(n)
    for k, q in enumerate(qs):
        lo, hi = br1_correspondence(float(q), M)
        p_lo[k] = lo
        p_hi[k] = hi
    return qs, p_lo, p_hi


def sample_br2_curve(M: PayoffMatrix, n: int = 501) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    ps = np.linspace(0.0, 1.0, n)
    q_lo = np.empty(n)
    q_hi = np.empty(n)
    for k, p in enumerate(ps):
        lo, hi = br2_correspondence(float(p), M)
        q_lo[k] = lo
        q_hi[k] = hi
    return ps, q_lo, q_hi
