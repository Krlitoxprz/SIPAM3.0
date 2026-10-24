"""Utilidades compartidas para el algoritmo de selección de monitores (RF-MON-05)."""


def calcular_puntaje(nota_asig: float, promedio: float, entrevista: float) -> float:
    """Fórmula RF-MON-05: (Nota_Asig * 0.30) + (Promedio * 0.30) + (Entrevista * 0.40)."""
    return round((nota_asig * 0.30) + (promedio * 0.30) + (entrevista * 0.40), 4)
