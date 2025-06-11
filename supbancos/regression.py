"""
Run OLS regressions of interest rates on concentration metrics and total cash systemwide.
Results are printed to stdout.
"""

import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd
import statsmodels.api as sm

from supbancos.fetch import get_eif_for_period, get_rate_series_xml
from supbancos.metrics import cash_equivalents_by_entity, concentration_metrics


def build_regression_df(months_back: int = 120, tipo_entidades=None) -> pd.DataFrame:
    """
    Build a DataFrame indexed by period (YYYY-MM) containing:
      - concentration metrics (hhi, cr3, gini) for cash-equivalents
      - total_cash: aggregate cash-equivalents systemwide
      - fitd_pa: short-term deposit rate (FITD_PA)
      - fii_pa: interbank rate (FII_PA)
    """
    end_period = datetime.today().strftime("%Y-%m")
    periods = []
    dt_end = datetime.strptime(end_period, "%Y-%m")
    for i in range(months_back):
        dt = dt_end - relativedelta(months=i)
        periods.append(dt.strftime("%Y-%m"))
    periods = list(reversed(periods))

    rows = []
    for per in periods:
        data = get_eif_for_period(per, entidades=None, tipo_entidades=tipo_entidades)
        if not data:
            continue
        amounts = cash_equivalents_by_entity(data)
        cm = concentration_metrics(amounts, top_n=3)
        cm["periodo"] = per
        cm["total_cash"] = sum(amounts.values())
        rows.append(cm)
    if not rows:
        raise RuntimeError("No data available to build regression dataset")

    df = pd.DataFrame(rows).set_index("periodo")

    fitd = get_rate_series_xml("FITD_PA")
    fii = get_rate_series_xml("FII_PA")
    df["fitd_pa"] = df.index.map(fitd.get)
    df["fii_pa"] = df.index.map(fii.get)

    df = df.dropna(subset=["fitd_pa", "fii_pa", "hhi", "cr3", "gini", "total_cash"])
    return df


def run_regression(df: pd.DataFrame, rate_col: str = "fitd_pa", indep_vars=None):
    """
    Run OLS regression of rate_col on the given independent variables.
    Returns the fitted statsmodels OLS Results instance.
    """
    if indep_vars is None:
        indep_vars = ["hhi", "cr3", "gini", "total_cash"]
    X = df[indep_vars]
    X = sm.add_constant(X)
    y = df[rate_col]
    model = sm.OLS(y, X).fit()
    return model


def main(months_back: int = 120):
    tipo_env = os.getenv("SB_TIPO_ENTIDADES")
    tipo_list = [t.strip() for t in tipo_env.split(",")] if tipo_env else None

    df = build_regression_df(months_back=months_back, tipo_entidades=tipo_list)
    print("\nRegression of FITD_PA (short-term deposit rate) on concentration & total cash:")
    res1 = run_regression(df, rate_col="fitd_pa")
    print(res1.summary())

    print("\nRegression of FII_PA (interbank rate) on concentration & total cash:")
    res2 = run_regression(df, rate_col="fii_pa")
    print(res2.summary())


if __name__ == "__main__":
    main()