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
    # Filter out the 'TODOS' category if present
    filtered = {k: v for k, v in aggregated.items() if k.upper() != "TODOS"}
    labels = list(filtered.keys())
    values = [filtered[k] for k in labels]
    fig, ax = plt.subplots()
    ax.bar(range(len(labels)), values)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_title(title)
    ax.set_ylabel("Valor")
    fig.tight_layout()
    return fig, ax


def aggregate_cash_equivalents(data_list):
    """
    Aggregate 'Efectivo y equivalentes de efectivo' (conceptoNivel2) by conceptoNivel3 subcategory.
    Filters out any 'TODOS' entries.
    Returns a dict mapping each subcategory to its total value.
    """
    result = {}
    for item in data_list:
        if item.get("conceptoNivel1") != "Activos":
            continue
        if item.get("conceptoNivel2") != "Efectivo y equivalentes de efectivo":
            continue
        sub = item.get("conceptoNivel3")
        if not sub or sub.upper() == "TODOS":
            continue
        result[sub] = result.get(sub, 0) + item.get("valor", 0)
    return result


def plot_cash_equivalents_by_institution(data_list, mapping=None, top_n=3, title=None):
    """
    Plot a stacked bar chart of cash and cash equivalents subcategories by institution.

    Each bar on the x-axis is a conceptoNivel3 subcategory (under 'Efectivo y equivalentes de efectivo').
    Within each bar, the top_n institutions (by total cash-equivalents) are highlighted with distinct colors
    (defaulting to Popular=BPD (blue), Reservas=BRS (green), and the third top institution (orange)),
    while all other institutions are grouped into 'Others' (gray).
    Returns (fig, ax).
    """
    default_mapping = {
        "BPD": ("Popular", "blue"),
        "BRS": ("Reservas", "green"),
    }
    if mapping:
        default_mapping.update(mapping)

    subcat_ent = {}
    for item in data_list:
        if item.get("conceptoNivel1") != "Activos":
            continue
        if item.get("conceptoNivel2") != "Efectivo y equivalentes de efectivo":
            continue
        subcat = item.get("conceptoNivel3")
        entidad = item.get("entidad")
        if not subcat or not entidad or subcat.upper() == "TODOS" or entidad.upper() == "TODOS":
            continue
        subcat_ent.setdefault(subcat, {})
        subcat_ent[subcat][entidad] = subcat_ent[subcat].get(entidad, 0) + item.get("valor", 0)

    if not subcat_ent:
        raise ValueError("No 'Efectivo y equivalentes de efectivo' data found")

    total_by_ent = {}
    for ent_vals in subcat_ent.values():
        for ent, val in ent_vals.items():
            total_by_ent[ent] = total_by_ent.get(ent, 0) + val
    sorted_ents = sorted(total_by_ent.items(), key=lambda kv: kv[1], reverse=True)
    top_ents = [ent for ent, _ in sorted_ents[:top_n]]

    total_by_sub = {sub: sum(vals.values()) for sub, vals in subcat_ent.items()}
    sorted_subcats = [sub for sub, _ in sorted(total_by_sub.items(), key=lambda kv: kv[1], reverse=True)]

    entities_plot = top_ents + ["Others"]
    palette = ["blue", "green", "orange"]
    labels = []
    colors = []
    for idx, ent in enumerate(entities_plot):
        if ent in default_mapping:
            lbl, clr = default_mapping[ent]
        elif ent == "Others":
            lbl, clr = "Others", "lightgray"
        elif idx < len(palette):
            lbl, clr = ent, palette[idx]
        else:
            lbl, clr = ent, "lightgray"
        labels.append(lbl)
        colors.append(clr)

    fig, ax = plt.subplots()
    bottom = [0] * len(sorted_subcats)
    for ent_idx, ent in enumerate(entities_plot):
        heights = []
        for sub in sorted_subcats:
            if ent == "Others":
                heights.append(sum(v for e, v in subcat_ent[sub].items() if e not in top_ents))
            else:
                heights.append(subcat_ent[sub].get(ent, 0))
        ax.bar(range(len(sorted_subcats)), heights, bottom=bottom, color=colors[ent_idx], label=labels[ent_idx])
        bottom = [b + h for b, h in zip(bottom, heights)]

    ax.set_xticks(range(len(sorted_subcats)))
    ax.set_xticklabels(sorted_subcats, rotation=45, ha="right")
    ax.set_ylabel("Valor")
    ax.set_title(title or "Efectivo y equivalentes de efectivo")
    ax.legend()
    fig.tight_layout()
    return fig, ax