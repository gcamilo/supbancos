# supbancos

Utilities to fetch financial statistics from the Dominican Republic Superintendencia de Bancos (SB) API and plot asset breakdowns.

## Prerequisites

- Python 3.7+
- A subscription key from the Superintendencia de Bancos (SB)

## Setup

1. Copy the example environment file and set your API key:
   ```bash
   cp .env.example .env
   # then edit .env and set:
   SB_API_KEY=your_subscription_key
   # (Optional) override list of tipoEntidad values if the API requires a filter:
   # SB_TIPO_ENTIDADES=BM,BAyC,CEF,APAP
   # By default, the script auto-discovers all available tipoEntidad values for the starting period.
   ```
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Local caching

To avoid re-downloading raw API responses and rate XML on every run, a local cache directory `cache/`
(gitignored) is used under the project root.  Raw JSON for each EIF period and the Central Bank XML
are stored here.  Subsequent script runs will reuse cached files if present.  To refresh data, remove
the relevant files under `cache/`.

## Usage

Generate and save the latest "Activos" bar chart (for the most recent period with data):
```bash
python -m supbancos.asset_chart
```
The script will:
- find the most recent period with available EIF data
- download and aggregate the "Activos" figures at nivel 2 for that period
- exclude the 'TODOS' aggregate category and focus on individual asset types
- save the bar chart as `assets_<YYYY-MM>_bar_chart.png` in your current directory

### Efectivo y equivalentes de efectivo breakdown

Generate and save the cash-equivalents stacked bar chart (breakdown by subcategory and institution shares):
```bash
python -m supbancos.cash_chart
```
The script will:
- find the most recent period with available EIF data
- download and filter the "Efectivo y equivalentes de efectivo" figures for that period
- break down these amounts by subcategory (conceptoNivel3) on the x-axis, with the y-axis representing total values
- within each bar, highlight the top 3 institutions (Popular = BPD (blue), Reservas = BRS (green), and the third top institution (orange)), and group all other institutions into an "Others" segment (gray)
- save the stacked bar chart as `cash_equivalents_<YYYY-MM>_bar_chart.png` in your current directory

## Concentration & interest rates over time

Generate and save concentration metrics (HHI, CR3, Gini) for "Efectivo y equivalentes de efectivo" over a rolling window alongside the short-term deposit rate (FITD_PA):

```bash
python -m supbancos.concentration_chart --months-back <N>
```

By default, this will:
- look back the last 120 months (10 years; configurable via the `--months-back` option)
- fetch cash-equivalents data for each period
- compute HHI, CR3, and Gini coefficients on the distribution of cash-equivalents across institutions
- fetch the FITD_PA (short-term deposit) and FII_PA (interbank) series from the Central Bank's XML feed and align them with the concentration metrics
- plot a two-panel figure:
  - top panel: HHI (circle), CR3 (square), and Gini (triangle) over time
  - bottom panel: FITD_PA and FII_PA rates over time
- save the chart as `concentration_rates_<start>_<end>.png`

## Testing

Run the test suite:
```bash
pytest -q
```

## Regression analysis of interest rates on concentration and cash

Run OLS regressions of the FITD_PA (short-term deposit) and FII_PA (interbank) rates
on the concentration metrics (HHI, CR3, Gini) and the aggregate amount of cash systemwide
over a rolling window.

```bash
python -m supbancos.regression --months-back <N>
```

By default, this will:
- look back 120 months (10 years; configurable via the `--months-back` option)
- fetch cash-equivalents data and compute concentration metrics & total cash each period
- fetch FITD_PA and FII_PA rates from the Central Bank XML feed
- build a pandas DataFrame and run two OLS regressions
- print the model summaries to stdout