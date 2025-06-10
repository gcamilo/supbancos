import pytest

from datetime import datetime

import supbancos.fetch as fetch_module


class DummyResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = str(data)

    def json(self):
        return self._data


@pytest.fixture(autouse=True)
def env_api_key(monkeypatch):
    monkeypatch.setenv("SB_API_KEY", "dummy_key")


def test_get_eif_for_period_success(monkeypatch):
    records = [{"conceptoNivel1": "Activos", "conceptoNivel2": "Foo", "valor": 100}]
    def fake_get(url, headers, params):
        return DummyResponse(records)

    monkeypatch.setattr(fetch_module.requests, "get", fake_get)
    data = fetch_module.get_eif_for_period("2021-01")
    assert data == records


def test_get_eif_for_period_no_api_key(monkeypatch):
    monkeypatch.delenv("SB_API_KEY", raising=False)
    with pytest.raises(fetch_module.SBAPIError):
        fetch_module.get_eif_for_period("2021-01")


def test_get_eif_for_period_http_error(monkeypatch):
    def fake_get(url, headers, params):
        return DummyResponse({"error": "fail"}, status_code=500)

    monkeypatch.setattr(fetch_module.requests, "get", fake_get)
    with pytest.raises(fetch_module.SBAPIError):
        fetch_module.get_eif_for_period("2021-01")


def test_find_latest_period(monkeypatch):
    calls = []
    def fake_get_eif(periodo, registros=1000):
        calls.append(periodo)
        return [] if periodo == "2021-06" else [{"a": 1}]

    monkeypatch.setattr(fetch_module, "get_eif_for_period", fake_get_eif)
    start = datetime(2021, 6, 30)
    periodo, data = fetch_module.find_latest_period(max_months_back=2, start_date=start)
    assert periodo == "2021-05"
    assert data == [{"a": 1}]
    assert calls == ["2021-06", "2021-05"]

def test_get_entities_for_period_success(monkeypatch):
    records = [
        {"entidad": "A", "detalle": "foo"},
        {"entidad": "B", "detalle": "bar"},
        {"entidad": "A", "detalle": "baz"},
    ]

    def fake_get(url, headers, params):
        return DummyResponse(records)

    monkeypatch.setattr(fetch_module.requests, "get", fake_get)
    entities = fetch_module.get_entities_for_period("2021-01")
    assert entities == ["A", "B"]

def test_get_entities_for_period_http_error(monkeypatch):
    def fake_get(url, headers, params):
        return DummyResponse({"error": "fail"}, status_code=500)

    monkeypatch.setenv("SB_API_KEY", "dummy_key")
    monkeypatch.setattr(fetch_module.requests, "get", fake_get)
    with pytest.raises(fetch_module.SBAPIError):
        fetch_module.get_entities_for_period("2021-01")

def test_find_latest_period_for_all_entities(monkeypatch):
    # Simulate entities and eif data: only period "2021-05" has full coverage
    entity_map = {
        "2021-06": ["X", "Y"],
        "2021-05": ["X", "Y"],
        "2021-04": ["X", "Y"],
    }
    # For 2021-06, eif returns data missing "Y"; for others, full
    def fake_get_entities(periodo, registros=1000):
        return entity_map[periodo]

    def fake_get_eif(periodo, registros=1000, entidades=None):
        if periodo == "2021-06":
            return [{"entidad": "X"}]
        return [{"entidad": "X"}, {"entidad": "Y"}]

    monkeypatch.setenv("SB_API_KEY", "dummy_key")
    monkeypatch.setattr(fetch_module, "get_entities_for_period", fake_get_entities)
    monkeypatch.setattr(fetch_module, "get_eif_for_period", fake_get_eif)

    periodo, entities, data = fetch_module.find_latest_period_for_all_entities(
        max_months_back=3, start_date=datetime(2021, 6, 1)
    )
    assert periodo == "2021-05"
    assert entities == ["X", "Y"]
    assert data == [{"entidad": "X"}, {"entidad": "Y"}]