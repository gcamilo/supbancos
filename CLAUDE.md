# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python package for fetching and analyzing financial statistics from the Dominican Republic's Superintendencia de Bancos (SB) API. The project focuses on asset breakdowns, concentration metrics, and interest rate analysis for the Dominican banking system.

## Core Architecture

- **supbancos/fetch.py**: Core API client with caching for SB API and Central Bank XML data
- **supbancos/metrics.py**: Financial concentration calculations (HHI, CR3, Gini coefficient)
- **supbancos/plot.py**: Shared plotting utilities and chart styling
- **supbancos/asset_chart.py**: Asset breakdown bar charts
- **supbancos/cash_chart.py**: Cash equivalents stacked charts with institutional breakdown
- **supbancos/concentration_chart.py**: Time series analysis of concentration metrics vs interest rates
- **supbancos/regression.py**: OLS regression analysis of rates on concentration and cash levels

## Common Commands

### Setup and Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment (requires SB API subscription key)
cp .env.example .env
# Edit .env to set SB_API_KEY=your_subscription_key
```

### Running Analysis Scripts
```bash
# Generate latest asset breakdown chart
python -m supbancos.asset_chart

# Generate cash equivalents breakdown chart
python -m supbancos.cash_chart

# Generate concentration metrics over time (default: 10 years)
python -m supbancos.concentration_chart --months-back 120

# Run regression analysis
python -m supbancos.regression --months-back 120
```

### Testing
```bash
# Run all tests
pytest -q

# Run specific test files
pytest tests/test_fetch.py
pytest tests/test_metrics.py
pytest tests/test_plot.py
```

## Data Sources and Caching

- **Primary API**: Superintendencia de Bancos (SB) EIF (Estado de Situación) endpoint
- **Secondary API**: Central Bank XML feed for interest rates (INR_DR.xml)
- **Local caching**: JSON files stored in `cache/` directory (gitignored)
- **Cache structure**: `cache/eif_YYYY-MM.json` for monthly EIF data, `cache/INR_DR.xml` for rates

## Key Data Concepts

- **EIF**: Estado de Información Financiera (Financial Information Statement)
- **Concentration metrics**: HHI (Herfindahl-Hirschman Index), CR3 (3-firm concentration ratio), Gini coefficient
- **Interest rates**: FITD_PA (short-term deposits), FII_PA (interbank rates)
- **Entity types**: BM, BAyC, CEF, APAP (different bank categories)

## Environment Variables

- `SB_API_KEY`: Required subscription key for SB API
- `SB_TIPO_ENTIDADES`: Optional override for entity types filter
- `SB_CACHE_DIR`: Cache directory (defaults to "cache")

## Testing Framework

Uses pytest with mock fixtures for API responses. Test files mirror the module structure and include comprehensive coverage for data fetching, metric calculations, and plotting functions.