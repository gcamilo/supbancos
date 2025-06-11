import sys

from .fetch import find_latest_period, SBAPIError
from .plot import plot_cash_equivalents_by_institution


def main():
    try:
        periodo, data = find_latest_period()
    except SBAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Fetched data for period {periodo} ({len(data)} records)")
    fig, ax = plot_cash_equivalents_by_institution(
        data, title=f"Efectivo y equivalentes de efectivo ({periodo})"
    )
    output_file = f"cash_equivalents_{periodo}_bar_chart.png"
    fig.savefig(output_file)
    print(f"Saved cash-equivalents bar chart to {output_file}")


if __name__ == "__main__":
    main()