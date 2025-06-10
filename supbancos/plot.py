import matplotlib.pyplot as plt


def aggregate_assets(data_list, level=2):
    """
    Aggregate 'Activos' values by conceptoNivel[level].

    level must be 1, 2, or 3.
    Returns a dict mapping each sub-concept to its total value.
    """
    if level not in (1, 2, 3):
        raise ValueError("level must be 1, 2, or 3")
    key_lvl1 = "conceptoNivel1"
    key_lvln = f"conceptoNivel{level}"
    result = {}
    for item in data_list:
        if item.get(key_lvl1) != "Activos":
            continue
        sub = item.get(key_lvln)
        if not sub:
            continue
        result[sub] = result.get(sub, 0) + item.get("valor", 0)
    return result


def plot_bar_chart(aggregated, title="Activos"):
    """
    Plot a bar chart from aggregated data.

    Returns (fig, ax).
    """
    labels = list(aggregated.keys())
    values = [aggregated[k] for k in labels]
    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel("Valor")
    ax.set_xticklabels(labels, rotation=45, ha="right")
    plt.tight_layout()
    return fig, ax