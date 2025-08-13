#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

def extract_government_deposit_data():
    """
    Extract government deposit data from the sectoral balance sheet Excel file.
    """
    print("Reading sectoral balance sheet data...")
    
    # Read the Excel file without headers first to understand structure
    df_raw = pd.read_excel('supbancos/balance_osd_pasivos.xlsx', header=None)
    
    # Find the header row (contains "Año/Mes")
    header_row = None
    for i, row in df_raw.iterrows():
        if pd.notnull(row[0]) and str(row[0]).strip() == 'Año/Mes':
            header_row = i
            break
    
    if header_row is None:
        raise ValueError("Could not find header row")
    
    print(f"Found header row at index: {header_row}")
    
    # Read the data starting from the header row
    df = pd.read_excel('supbancos/balance_osd_pasivos.xlsx', header=header_row, skiprows=1)
    
    # Clean column names - based on the structure we saw:
    # Column 0: Year, Column 1: Month
    # Column 4: Gobierno central (Central Government deposits)  
    # Column 2-8: Other deposit categories that make up total deposits
    
    # The columns should be aligned as follows based on our examination:
    # (1) No residentes, (2) Otras sociedades de depósito, (3) Otras sociedades financieras,
    # (4) Gobierno central, (5) Gobiernos estatales y locales, etc.
    
    # Clean the dataframe
    df = df.dropna(subset=[df.columns[0]])  # Remove rows where year is NaN
    
    # Convert year and month to datetime
    df['Year'] = pd.to_numeric(df[df.columns[0]], errors='coerce')
    df['Month'] = df[df.columns[1]]
    
    # Convert month names to numbers (assuming Spanish month names)
    month_map = {
        'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12
    }
    
    df['MonthNum'] = df['Month'].map(month_map)
    
    # Only create date for rows where MonthNum is valid
    df = df.dropna(subset=['MonthNum'])
    
    # Create datetime column more robustly
    df = df.reset_index(drop=True)  # Reset index after dropping rows
    df['Date'] = pd.to_datetime(df['Year'].astype(int).astype(str) + '-' + 
                               df['MonthNum'].astype(int).astype(str) + '-01')
    
    # Use named columns now that we have them
    gov_deposits_col = 'Gobierno central'
    
    # Calculate total deposits as sum of all deposit categories
    # Based on the structure: columns 2-9 are deposit categories
    deposit_columns = ['No residentes', 'Otras sociedades de depósito', 'Otras sociedades financieras',
                      'Gobierno central', 'Gobiernos estatales y locales', 'Sociedades públicas no financieras', 
                      'Otras sociedades no financieras', 'Hogares e ISFLSH']
    
    # Extract the data
    results = []
    for idx, row in df.iterrows():
        if pd.notnull(row['Date']):
            try:
                # Government deposits
                gov_deposits = pd.to_numeric(row[gov_deposits_col], errors='coerce')
                
                # Total deposits (sum of all deposit categories)
                total_deposits = 0
                for col_name in deposit_columns:
                    if col_name in df.columns:
                        deposit_val = pd.to_numeric(row[col_name], errors='coerce')
                        if pd.notnull(deposit_val):
                            total_deposits += deposit_val
                
                if pd.notnull(gov_deposits) and total_deposits > 0:
                    gov_share = gov_deposits / total_deposits
                    results.append({
                        'Date': row['Date'],
                        'Year': row['Year'],
                        'Month': row['Month'],
                        'GovernmentDeposits': gov_deposits,
                        'TotalDeposits': total_deposits,
                        'GovernmentShare': gov_share
                    })
                    
            except Exception as e:
                print(f"Error processing row {idx}: {e}")
                continue
    
    return pd.DataFrame(results)

def create_government_deposit_chart(df):
    """
    Create visualization of government deposit share over time.
    """
    if df.empty:
        print("No data available for visualization")
        return
        
    # Sort by date
    df = df.sort_values('Date')
    
    # Filter to last 10 years for clarity
    cutoff_date = datetime.now().replace(year=datetime.now().year - 10)
    df_recent = df[df['Date'] >= cutoff_date].copy()
    
    # Create the visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Top panel: Government deposit share as percentage
    ax1.plot(df_recent['Date'], df_recent['GovernmentShare'] * 100, 
             'b-', linewidth=2, marker='o', markersize=2, alpha=0.7)
    ax1.set_title('Banreservas: Government Deposits as Share of Total Deposits\n(Last 10 Years)', 
                  fontsize=14, fontweight='bold', pad=20)
    ax1.set_ylabel('Government Deposit Share (%)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, max(df_recent['GovernmentShare'] * 100) * 1.1)
    
    # Format x-axis
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_minor_locator(mdates.MonthLocator((1, 7)))
    
    # Bottom panel: Absolute amounts in billions
    ax2.plot(df_recent['Date'], df_recent['TotalDeposits'] / 1000, 
             'g-', linewidth=2, label='Total Deposits', marker='s', markersize=2, alpha=0.7)
    ax2.plot(df_recent['Date'], df_recent['GovernmentDeposits'] / 1000, 
             'r-', linewidth=2, label='Government Deposits', marker='^', markersize=2, alpha=0.7)
    
    ax2.set_title('Banreservas: Deposit Amounts Over Time', fontsize=14, fontweight='bold', pad=20)
    ax2.set_ylabel('Deposits (Billion DOP)', fontsize=12)
    ax2.set_xlabel('Year', fontsize=12)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.xaxis.set_minor_locator(mdates.MonthLocator((1, 7)))
    
    # Rotate x-axis labels
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Save the chart
    output_file = 'banreservas_government_deposits_share.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Chart saved as {output_file}")
    
    return output_file

def print_summary_statistics(df):
    """
    Print summary statistics about government deposit share.
    """
    if df.empty:
        print("No data available for statistics")
        return
        
    print(f"\n=== SUMMARY STATISTICS ===")
    print(f"Data period: {df['Date'].min().strftime('%Y-%m')} to {df['Date'].max().strftime('%Y-%m')}")
    print(f"Total observations: {len(df)}")
    
    gov_share_pct = df['GovernmentShare'] * 100
    print(f"\nGovernment Deposit Share:")
    print(f"  Mean: {gov_share_pct.mean():.1f}%")
    print(f"  Median: {gov_share_pct.median():.1f}%")
    print(f"  Min: {gov_share_pct.min():.1f}% ({df.loc[gov_share_pct.idxmin(), 'Date'].strftime('%Y-%m')})")
    print(f"  Max: {gov_share_pct.max():.1f}% ({df.loc[gov_share_pct.idxmax(), 'Date'].strftime('%Y-%m')})")
    print(f"  Std Dev: {gov_share_pct.std():.1f}%")
    
    # Recent trends (last 5 years)
    recent_df = df[df['Date'] >= datetime.now().replace(year=datetime.now().year - 5)]
    if not recent_df.empty:
        recent_mean = (recent_df['GovernmentShare'] * 100).mean()
        print(f"\nRecent 5-year average: {recent_mean:.1f}%")
        
        # Calculate trend
        x = np.arange(len(recent_df))
        y = recent_df['GovernmentShare'] * 100
        slope = np.polyfit(x, y, 1)[0] * 12  # Annualized trend
        trend_direction = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
        print(f"Recent trend: {trend_direction} (±{abs(slope):.1f}% per year)")

if __name__ == "__main__":
    try:
        # Extract data from Excel file
        df = extract_government_deposit_data()
        
        if not df.empty:
            print(f"Successfully extracted {len(df)} data points")
            
            # Print summary statistics
            print_summary_statistics(df)
            
            # Create visualization
            output_file = create_government_deposit_chart(df)
            
            # Save data for future analysis
            df.to_csv('banreservas_government_deposits_data.csv', index=False)
            print("Data saved to banreservas_government_deposits_data.csv")
            
            # Show recent data
            print(f"\n=== RECENT DATA (Last 12 months) ===")
            recent = df.tail(12)
            for _, row in recent.iterrows():
                print(f"{row['Date'].strftime('%Y-%m')}: {row['GovernmentShare']*100:.1f}% "
                      f"(Gov: {row['GovernmentDeposits']:,.0f}M, Total: {row['TotalDeposits']:,.0f}M)")
                
        else:
            print("No valid data found in the Excel file")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()