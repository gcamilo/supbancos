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

Generate and save the latest "Activos" bar chart:
```bash
python -m supbancos.asset_chart
```
This will save a PNG file named `assets_<YYYY-MM>_bar_chart.png` in your current directory.

## Testing

Run the test suite:
```bash
pytest -q
```