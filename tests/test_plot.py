import matplotlib
matplotlib.use("Agg")

import pytest

from supbancos.plot import aggregate_assets, plot_bar_chart


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