import sys

from .fetch import find_latest_period, SBAPIError
from .plot import aggregate_assets, plot_bar_chart


def main():
    try:
        periodo, data = find_latest_period()
    except SBAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Fetched data for period {periodo} ({len(data)} records)")
    agg = aggregate_assets(data, level=2)
    fig, ax = plot_bar_chart(agg, title=f"Activos ({periodo})")
    output_file = f"assets_{periodo}_bar_chart.png"
    fig.savefig(output_file)
    print(f"Saved bar chart to {output_file}")


if __name__ == "__main__":
    main()