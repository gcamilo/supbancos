# supbancos

Utilities to fetch financial statistics from the Dominican Republic bank regulator API and plot asset breakdowns.

## Prerequisites

- Python 3.7+
- A subscription key from the Superintendencia del Sistema Financiero (SSF)

## Setup

1. Copy the example environment file and set your API key:
   ```bash
   cp .env.example .env
   # then edit .env and set:
   SB_API_KEY=your_subscription_key
   # (Optional) override list of tipoEntidad values if the API requires a filter:
   # SB_TIPO_ENTIDADES=BM,BAyC,CEF,APAP
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

## Usage

Generate and save the latest "Activos" bar chart (for the most recent period with data):
```bash
python -m supbancos.asset_chart
```
The script will:
- find the most recent period with available EIF data
- download and aggregate the "Activos" figures at nivel 2 for that period
- save the bar chart as `assets_<YYYY-MM>_bar_chart.png` in your current directory

## Testing

Run the test suite:
```bash
pytest -q
```