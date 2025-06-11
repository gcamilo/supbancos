import pytest

from supbancos.metrics import gini, hhi, crn, concentration_metrics, cash_equivalents_by_entity


def test_gini_empty_and_zero():
    assert gini([]) == 0.0
    assert gini([0, 0, 0]) == 0.0


def test_gini_simple_cases():
    assert pytest.approx(gini([1]), rel=1e-9) == 0.0
    assert pytest.approx(gini([0, 1]), rel=1e-9) == 0.5
    # increasing sequence
    assert 0.0 <= gini([1, 2, 3]) <= 1.0


def test_hhi_and_crn_values():
    vals = [100, 100, 0]
    # shares [0.5, 0.5, 0], HHI = 0.25 + 0.25 = 0.5
    assert pytest.approx(hhi(vals), rel=1e-9) == 0.5
    # CR3 sums all shares -> 1.0
    assert pytest.approx(crn(vals, n=3), rel=1e-9) == 1.0
    # CR1 is only the largest share -> 0.5
    assert pytest.approx(crn(vals, n=1), rel=1e-9) == 0.5


def test_concentration_metrics():
    amounts = {"A": 60, "B": 30, "C": 10}
    cm = concentration_metrics(amounts, top_n=2)
    # total = 100, shares = [0.6, 0.3, 0.1]
    # HHI = 0.36 + 0.09 + 0.01 = 0.46
    assert pytest.approx(cm["hhi"], rel=1e-9) == 0.46
    # CR2 = 0.6 + 0.3 = 0.9
    assert pytest.approx(cm["cr2"], rel=1e-9) == 0.9
    # Gini is between 0 and 1
    assert 0.0 <= cm["gini"] <= 1.0


def test_cash_equivalents_by_entity():
    data = [
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "entidad": "X", "valor": 10},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "entidad": "Y", "valor": 5},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "entidad": "X", "valor": 3},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "entidad": "TODOS", "valor": 100},
        {"conceptoNivel1": "Pasivos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "entidad": "Z", "valor": 7},
    ]
    result = cash_equivalents_by_entity(data)
    assert result == {"X": 13.0, "Y": 5.0}