from typing import Dict, List

def gini(values: List[float]) -> float:
    """
    Compute the Gini coefficient of a list of values.
    Returns 0 for empty or all-zero lists.
    """
    n = len(values)
    if n == 0:
        return 0.0
    sorted_vals = sorted(values)
    cum_sum = 0.0
    for i, v in enumerate(sorted_vals, start=1):
        cum_sum += i * v
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    return (2 * cum_sum / total - (n + 1)) / n

def hhi(values: List[float]) -> float:
    """
    Compute the Herfindahl–Hirschman Index (HHI) for a list of market shares.
    Shares must sum to 1 (or will be normalized).
    Returns a value between 0 and 1.
    """
    total = sum(values)
    if total == 0:
        return 0.0
    shares = [v / total for v in values]
    return sum(s * s for s in shares)

def crn(values: List[float], n: int = 3) -> float:
    """
    Compute the concentration ratio CR_n: sum of the top-n shares.
    Shares will be normalized to sum to 1.
    """
    total = sum(values)
    if total == 0:
        return 0.0
    shares = sorted((v / total for v in values), reverse=True)
    return sum(shares[:n])

def concentration_metrics(amounts: Dict[str, float], top_n: int = 3) -> Dict[str, float]:
    """
    Given a mapping of entity -> amount, compute concentration metrics:
      - hhi: Herfindahl–Hirschman Index
      - cr3: concentration ratio of top_n entities
      - gini: Gini coefficient
    Returns a dict with keys 'hhi', 'cr<top_n>', and 'gini'.
    """
    vals = list(amounts.values())
    return {
        "hhi": hhi(vals),
        f"cr{top_n}": crn(vals, n=top_n),
        "gini": gini(vals),
    }

def cash_equivalents_by_entity(data_list: List[Dict]) -> Dict[str, float]:
    """
    Sum 'Efectivo y equivalentes de efectivo' (conceptoNivel2) values by entidad.
    Filters out any 'TODOS' entries.
    """
    result: Dict[str, float] = {}
    for item in data_list:
        if item.get("conceptoNivel1") != "Activos":
            continue
        if item.get("conceptoNivel2") != "Efectivo y equivalentes de efectivo":
            continue
        ent = item.get("entidad")
        if not ent or ent.upper() == "TODOS":
            continue
        result[ent] = result.get(ent, 0.0) + item.get("valor", 0.0)
    return result