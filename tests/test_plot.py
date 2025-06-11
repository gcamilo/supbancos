import matplotlib
matplotlib.use("Agg")

import pytest

from supbancos.plot import (
    aggregate_assets,
    plot_bar_chart,
    aggregate_cash_equivalents,
    plot_cash_equivalents_by_institution,
)


def test_aggregate_assets_level2():
    data = [
        {"conceptoNivel1": "Activos", "conceptoNivel2": "A", "valor": 10},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "B", "valor": 20},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "A", "valor": 5},
        {"conceptoNivel1": "Pasivos", "conceptoNivel2": "A", "valor": 100},
    ]
    agg = aggregate_assets(data, level=2)
    assert agg == {"A": 15, "B": 20}


def test_aggregate_assets_level3_missing_levels():
    data = [
        {"conceptoNivel1": "Activos", "conceptoNivel3": "C", "valor": 7},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "B", "valor": 3},
    ]
    agg = aggregate_assets(data, level=3)
    assert agg == {"C": 7}


def test_plot_bar_chart(tmp_path):
    data = {"A": 10, "B": 20}
    fig, ax = plot_bar_chart(data, title="Test")
    bars = ax.patches
    heights = sorted([b.get_height() for b in bars])
    assert heights == [10, 20]
    out = tmp_path / "chart.png"
    fig.savefig(out)
    assert out.exists()

def test_aggregate_cash_equivalents():
    data = [
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "conceptoNivel3": "Foo", "valor": 10},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "conceptoNivel3": "Bar", "valor": 20},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Pasivos", "conceptoNivel3": "Foo", "valor": 100},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "conceptoNivel3": "Foo", "valor": 5},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "conceptoNivel3": "TODOS", "valor": 100},
    ]
    agg = aggregate_cash_equivalents(data)
    assert agg == {"Foo": 15, "Bar": 20}


def test_plot_cash_equivalents_by_institution(tmp_path):
    # Prepare data for two subcategories and three institutions
    data_list = [
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "conceptoNivel3": "Foo", "entidad": "BPD", "valor": 10},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "conceptoNivel3": "Foo", "entidad": "BRS", "valor": 20},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "conceptoNivel3": "Foo", "entidad": "XYZ", "valor": 5},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "conceptoNivel3": "Bar", "entidad": "BPD", "valor": 30},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "conceptoNivel3": "Bar", "entidad": "BRS", "valor": 10},
        {"conceptoNivel1": "Activos", "conceptoNivel2": "Efectivo y equivalentes de efectivo", "conceptoNivel3": "Bar", "entidad": "XYZ", "valor": 5},
    ]
    custom_map = {"XYZ": ("XyzBank", "purple")}
    fig, ax = plot_cash_equivalents_by_institution(data_list, mapping=custom_map)
    # Expect two bars sorted by total descending (Bar then Foo)
    xticklabels = [t.get_text() for t in ax.get_xticklabels()]
    assert xticklabels == ["Bar", "Foo"]
    # There should be 4 segments per bar: BPD, BRS, XYZ, Others
    patches = ax.patches
    n_subcats = len(ax.get_xticklabels())
    n_ents = len(patches) // n_subcats
    assert n_ents == 4
    assert len(patches) == n_ents * n_subcats
    import matplotlib.colors as mcolors
    # Extract the segments for the first subcategory/bar (Bar)
    first_bar = [patches[i] for i in range(0, len(patches), n_subcats)]
    colors = [mcolors.to_hex(p.get_facecolor()) for p in first_bar]
    heights = [p.get_height() for p in first_bar]
    assert colors == [
        mcolors.to_hex(mcolors.to_rgba("blue")),
        mcolors.to_hex(mcolors.to_rgba("green")),
        mcolors.to_hex(mcolors.to_rgba("purple")),
        mcolors.to_hex(mcolors.to_rgba("lightgray")),
    ]
    assert heights == [30, 10, 5, 0]
    out = tmp_path / "cash.png"
    fig.savefig(out)
    assert out.exists()