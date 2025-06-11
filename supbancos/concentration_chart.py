"""
Generate concentration metrics (HHI, CRn, Gini) for cash equivalents over time
and compare against the FITD_PA short-term deposit rate and FII_PA interbank rate series from the Central Bank.
"""
import os
from datetime import datetime

import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta

from supbancos.fetch import get_eif_for_period, get_rate_series_xml
from supbancos.metrics import cash_equivalents_by_entity, concentration_metrics


def generate_period_list(end_period: str, months_back: int = 120):
    """
    Generate a list of YYYY-MM strings ending at end_period, going back months_back months.
    """
    dt_end = datetime.strptime(end_period, "%Y-%m")
    periods = []
    for i in range(months_back):
        dt = dt_end - relativedelta(months=i)
        periods.append(dt.strftime("%Y-%m"))
    return list(reversed(periods))


def main(months_back: int = 120):
    tipo_env = os.getenv("SB_TIPO_ENTIDADES")
    tipo_list = [t.strip() for t in tipo_env.split(",")] if tipo_env else None

    today = datetime.today()
    end_period = today.strftime("%Y-%m")
    periods = generate_period_list(end_period, months_back)

    metrics_rows = []
    for per in periods:
        data = get_eif_for_period(per, entidades=None, tipo_entidades=tipo_list)
        amounts = cash_equivalents_by_entity(data)
        cm = concentration_metrics(amounts, top_n=3)
        cm["periodo"] = per
        metrics_rows.append(cm)

    short_rates = get_rate_series_xml("FITD_PA")
    interbank_rates = get_rate_series_xml("FII_PA")

    present = {row["periodo"] for row in metrics_rows}
    common = present & set(short_rates) & set(interbank_rates)
    if common != present:
        missing_short = sorted(present - set(short_rates))
        missing_inter = sorted(present - set(interbank_rates))
        if missing_short:
            print(f"Warning: missing FITD_PA rates for periods: {missing_short}")
        if missing_inter:
            print(f"Warning: missing FII_PA rates for periods: {missing_inter}")
    metrics_rows = [row for row in metrics_rows if row["periodo"] in common]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    xs = [row["periodo"] for row in metrics_rows]
    ax1.plot(xs, [row["hhi"] for row in metrics_rows], label="HHI", marker="o")
    ax1.plot(xs, [row["cr3"] for row in metrics_rows], label="CR3", marker="s")
    ax1.plot(xs, [row["gini"] for row in metrics_rows], label="Gini", marker="^")
    ax1.set_ylabel("Concentration (0–1)")
    ax1.set_title("Cash-equivalents concentration metrics over time")
    ax1.legend()

    ax2.plot(xs, [short_rates[p] for p in xs], label="FITD_PA (short-term deposit rate)", color="tab:blue")
    ax2.plot(xs, [interbank_rates[p] for p in xs], label="FII_PA (interbank rate)", color="tab:orange")
    ax2.set_ylabel("Rate (%)")
    ax2.set_title("Short-term deposit (FITD_PA) and interbank (FII_PA) rates over time")
    ax2.legend()

    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()

    out_name = f"concentration_rates_{periods[0]}_{periods[-1]}.png"
    fig.savefig(out_name)
    print(f"Saved concentration & rates chart to {out_name}")


if __name__ == "__main__":
    main()