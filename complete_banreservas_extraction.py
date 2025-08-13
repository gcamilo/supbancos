#!/usr/bin/env python3

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

def extract_all_banreservas_data():
    """
    Extract ALL available Banreservas data from cached files (2012-2025).
    Focus on central bank assets and government deposits.
    """
    cache_dir = 'cache'
    
    # Get all files with BANRESERVAS data
    print("Finding all cached files with BANRESERVAS data...")
    banreservas_files = []
    
    # Check each cache file for BANRESERVAS data
    for cache_file in sorted(os.listdir(cache_dir)):
        if cache_file.startswith('eif_') and cache_file.endswith('.json'):
            try:
                with open(os.path.join(cache_dir, cache_file), 'r') as f:
                    content = f.read()
                    if 'BANRESERVAS' in content:
                        period = cache_file.replace('eif_', '').replace('.json', '')
                        banreservas_files.append(period)
            except:
                pass
    
    print(f"Found BANRESERVAS data in {len(banreservas_files)} periods: {banreservas_files[0]} to {banreservas_files[-1]}")
    
    # Load government deposits data
    gov_deposits_data = {}
    try:
        gov_df = pd.read_csv('banreservas_government_deposits_data.csv')
        gov_df['Date'] = pd.to_datetime(gov_df['Date'])
        gov_df['period'] = gov_df['Date'].dt.strftime('%Y-%m')
        for _, row in gov_df.iterrows():
            gov_deposits_data[row['period']] = {
                'government_deposits': row['GovernmentDeposits'] * 1e6,
                'government_share': row['GovernmentShare']
            }
        print(f"Government deposit data available for {len(gov_deposits_data)} periods")
    except FileNotFoundError:
        print("Government deposits file not found")
    
    results = []
    
    for period in banreservas_files:
        cache_file = f'eif_{period}.json'
        
        try:
            with open(os.path.join(cache_dir, cache_file), 'r') as f:
                data = json.load(f)
            
            # Extract Banreservas records
            banreservas_data = [d for d in data if d.get('entidad') == 'BANRESERVAS']
            
            if not banreservas_data:
                continue
            
            # Initialize balance sheet components
            balance_sheet = {
                'banco_central_asset': 0,
                'caja': 0,
                'bancos_pais': 0, 
                'bancos_exterior': 0,
                'equivalentes_efectivo': 0,
                'total_efectivo_todos': 0,
                'total_deposits': 0,
                'depositos_vista': 0,
                'depositos_ahorro': 0,
                'depositos_plazo': 0,
                'banco_central_liability': 0,
                'total_activos': 0,
                'total_pasivos': 0
            }
            
            # Process all records
            for record in banreservas_data:
                concept1 = record.get('conceptoNivel1', '')
                concept2 = record.get('conceptoNivel2', '')
                concept3 = record.get('conceptoNivel3', '')
                valor = record.get('valor', 0)
                
                # Assets: Cash and Cash Equivalents
                if concept1 == 'Activos' and concept2 == 'Efectivo y equivalentes de efectivo':
                    if concept3 == 'Banco central':
                        balance_sheet['banco_central_asset'] = valor
                    elif concept3 == 'Caja':
                        balance_sheet['caja'] = valor
                    elif concept3 == 'Bancos del país':
                        balance_sheet['bancos_pais'] = valor
                    elif concept3 == 'Bancos del exterior':
                        balance_sheet['bancos_exterior'] = valor
                    elif concept3 == 'Equivalentes de efectivo':
                        balance_sheet['equivalentes_efectivo'] = valor
                    elif concept3 == 'TODOS':
                        balance_sheet['total_efectivo_todos'] = valor
                
                # Total Assets
                if concept1 == 'Activos' and concept2 == 'TODOS':
                    balance_sheet['total_activos'] = valor
                
                # Total Liabilities  
                if concept1 == 'Pasivos' and concept2 == 'TODOS':
                    balance_sheet['total_pasivos'] = valor
                
                # Deposits from Public
                if concept1 == 'Pasivos' and 'Depósitos del público' in concept2:
                    if concept3 == 'TODOS' or concept2 == 'Depósitos del público':
                        balance_sheet['total_deposits'] += valor
                    elif 'vista' in concept3.lower():
                        balance_sheet['depositos_vista'] = valor
                    elif 'ahorro' in concept3.lower(): 
                        balance_sheet['depositos_ahorro'] = valor
                    elif 'plazo' in concept3.lower():
                        balance_sheet['depositos_plazo'] = valor
                
                # Central Bank Liabilities
                if concept1 == 'Pasivos' and 'Banco Central' in concept2:
                    balance_sheet['banco_central_liability'] += valor
            
            # Calculate derived metrics
            total_liquid_assets = balance_sheet['total_efectivo_todos'] if balance_sheet['total_efectivo_todos'] > 0 else (
                balance_sheet['banco_central_asset'] + balance_sheet['caja'] + 
                balance_sheet['bancos_pais'] + balance_sheet['bancos_exterior'] + 
                balance_sheet['equivalentes_efectivo']
            )
            
            # Net CB position
            net_cb_position = balance_sheet['banco_central_asset'] - balance_sheet['banco_central_liability']
            
            # Government deposits from Excel data
            gov_data = gov_deposits_data.get(period, {'government_deposits': 0, 'government_share': 0})
            
            # Ratios
            cb_to_deposits_ratio = (balance_sheet['banco_central_asset'] / balance_sheet['total_deposits'] * 100) if balance_sheet['total_deposits'] > 0 else 0
            
            # Create record
            results.append({
                'period': period,
                'date': datetime.strptime(period + '-01', '%Y-%m-%d'),
                'banco_central_asset': balance_sheet['banco_central_asset'],
                'banco_central_liability': balance_sheet['banco_central_liability'],
                'net_cb_position': net_cb_position,
                'caja': balance_sheet['caja'],
                'bancos_pais': balance_sheet['bancos_pais'],
                'bancos_exterior': balance_sheet['bancos_exterior'],
                'equivalentes_efectivo': balance_sheet['equivalentes_efectivo'],
                'total_liquid_assets': total_liquid_assets,
                'total_deposits': balance_sheet['total_deposits'],
                'depositos_vista': balance_sheet['depositos_vista'],
                'depositos_ahorro': balance_sheet['depositos_ahorro'],
                'depositos_plazo': balance_sheet['depositos_plazo'],
                'total_activos': balance_sheet['total_activos'],
                'total_pasivos': balance_sheet['total_pasivos'],
                'government_deposits': gov_data['government_deposits'],
                'government_share_pct': gov_data['government_share'],
                'cb_to_deposits_ratio': cb_to_deposits_ratio,
                'has_cb_data': balance_sheet['banco_central_asset'] > 0,
                'has_deposit_data': balance_sheet['total_deposits'] > 0
            })
            
        except Exception as e:
            print(f"Error processing {period}: {e}")
            continue
    
    print(f"\nExtracted data for {len(results)} periods")
    
    # Create DataFrame and analyze
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('date')
        
        cb_periods = df[df['has_cb_data'] == True]
        deposit_periods = df[df['has_deposit_data'] == True]
        gov_periods = df[df['government_deposits'] > 0]
        
        print(f"\nData Summary:")
        print(f"  Total periods: {len(df)}")
        print(f"  Periods with CB asset data: {len(cb_periods)}")
        print(f"  Periods with deposit data: {len(deposit_periods)}")
        print(f"  Periods with government deposits: {len(gov_periods)}")
        print(f"  Date range: {df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}")
        
        if len(cb_periods) > 0:
            cb_stats = cb_periods['banco_central_asset'] / 1e9
            print(f"\nCB Asset Statistics (when > 0, Billion DOP):")
            print(f"  Count: {len(cb_periods)}")
            print(f"  Mean: {cb_stats.mean():.1f}")
            print(f"  Range: {cb_stats.min():.1f} - {cb_stats.max():.1f}")
    
    return df

def create_complete_10year_analysis(df):
    """
    Create complete 10-year analysis with all available data.
    """
    if df.empty:
        print("No data for analysis")
        return None
    
    # Filter to last 10 years
    cutoff_date = datetime.now() - timedelta(days=10*365)
    df_10y = df[df['date'] >= cutoff_date].copy()
    df_10y = df_10y.sort_values('date')
    
    print(f"\n10-year analysis: {len(df_10y)} observations from {df_10y['date'].min().strftime('%Y-%m')} to {df_10y['date'].max().strftime('%Y-%m')}")
    
    # Apply realistic CB estimates where actual data is missing
    def get_realistic_cb_liquidity(row):
        if row['banco_central_asset'] > 0:
            return row['banco_central_asset']
        
        # Estimate based on deposits and liquid assets
        total_deposits = row['total_deposits']
        gov_deposits = row['government_deposits']
        total_liquid = row['total_liquid_assets']
        
        estimated = 0
        
        if total_deposits > 0:
            estimated = max(estimated, total_deposits * 0.15)  # 15% reserve requirement
        
        if gov_deposits > 0:
            estimated = max(estimated, gov_deposits * 0.20)  # Higher for gov transactions
        
        if total_liquid > 0:
            estimated = max(estimated, total_liquid * 0.30)  # 30% of liquid assets
        
        # Minimum for major Dominican bank
        estimated = max(estimated, 30e9)  # 30B DOP minimum
        
        return estimated
    
    df_10y['realistic_cb_liquidity'] = df_10y.apply(get_realistic_cb_liquidity, axis=1)
    
    # Recalculate government share
    df_10y['gov_share_pct'] = df_10y.apply(
        lambda row: (row['government_deposits'] / row['total_deposits'] * 100) 
        if row['total_deposits'] > 0 else 0, axis=1
    )
    
    # Data quality check
    zero_cb = (df_10y['realistic_cb_liquidity'] == 0).sum()
    print(f"Zero CB liquidity periods after correction: {zero_cb}")
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 14))
    
    # Panel 1: CB Liquidity vs Government Deposits
    ax1_twin = ax1.twinx()
    
    # Plot CB liquidity
    cb_line = ax1.plot(df_10y['date'], df_10y['realistic_cb_liquidity'] / 1e9, 
                      'b-', linewidth=3, alpha=0.9, label='CB Liquidity (1.a.2)')
    
    # Plot government deposits  
    gov_line = ax1_twin.plot(df_10y['date'], df_10y['government_deposits'] / 1e9,
                           'r-', linewidth=3, alpha=0.9, label='Government Deposits')
    
    # Mark actual vs estimated CB data
    actual_cb = df_10y[df_10y['banco_central_asset'] > 0]
    estimated_cb = df_10y[df_10y['banco_central_asset'] == 0]
    
    if not actual_cb.empty:
        ax1.scatter(actual_cb['date'], actual_cb['realistic_cb_liquidity'] / 1e9,
                   color='darkblue', s=50, alpha=0.8, zorder=5, label='Actual CB Data')
    
    if not estimated_cb.empty:
        ax1.scatter(estimated_cb['date'], estimated_cb['realistic_cb_liquidity'] / 1e9,
                   color='lightblue', s=30, alpha=0.7, zorder=4, label='Estimated CB', marker='^')
    
    ax1.set_title('Banreservas: Central Bank Liquidity vs Government Deposits (Complete 10-Year Data)', 
                  fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel('CB Liquidity (Billion DOP)', color='blue', fontsize=14, fontweight='bold')
    ax1_twin.set_ylabel('Government Deposits (Billion DOP)', color='red', fontsize=14, fontweight='bold')
    
    ax1.tick_params(axis='y', labelcolor='blue', labelsize=12)
    ax1_twin.tick_params(axis='y', labelcolor='red', labelsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Correlation and stats
    correlation = df_10y['realistic_cb_liquidity'].corr(df_10y['government_deposits'])
    ax1.text(0.02, 0.98, f'Correlation: {correlation:.3f}\n'
                         f'Actual CB data: {len(actual_cb)} periods\n'
                         f'Estimated: {len(estimated_cb)} periods', 
            transform=ax1.transAxes, fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='wheat', alpha=0.9),
            verticalalignment='top')
    
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12)
    
    # Panel 2: Government Share of Deposits
    ax2.plot(df_10y['date'], df_10y['gov_share_pct'], 
             'g-', linewidth=3, alpha=0.9, label='Government Share')
    ax2.fill_between(df_10y['date'], 0, df_10y['gov_share_pct'], 
                     alpha=0.3, color='green')
    
    # Trend line
    if len(df_10y) > 2:
        x_numeric = np.arange(len(df_10y))
        z = np.polyfit(x_numeric, df_10y['gov_share_pct'], 1)
        p = np.poly1d(z)
        trend_slope = z[0] * 12  # Annual trend
        ax2.plot(df_10y['date'], p(x_numeric), 'r--', alpha=0.8, linewidth=2,
                label=f'Trend ({trend_slope:+.1f}%/year)')
    
    # Average line
    avg_share = df_10y['gov_share_pct'].mean()
    ax2.axhline(y=avg_share, color='orange', linestyle=':', alpha=0.8, linewidth=2,
               label=f'Average ({avg_share:.1f}%)')
    
    ax2.set_title('Government Share of Total Deposits (Complete Data)', 
                  fontsize=16, fontweight='bold', pad=20)
    ax2.set_ylabel('Government Share (%)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right', fontsize=12)
    
    # Statistics box
    recent_12m = df_10y.tail(12)['gov_share_pct'].mean()
    ax2.text(0.02, 0.98, 
            f'Recent 12-month avg: {recent_12m:.1f}%\n'
            f'10-year range: {df_10y["gov_share_pct"].min():.1f}% - {df_10y["gov_share_pct"].max():.1f}%\n'
            f'Data points: {len(df_10y)} months', 
            transform=ax2.transAxes, fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgreen', alpha=0.9),
            verticalalignment='top')
    
    # Format dates
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_minor_locator(mdates.MonthLocator((1, 7)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, fontsize=12)
    
    plt.tight_layout()
    
    # Save
    output_file = 'banreservas_complete_10year_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\nComplete 10-year analysis saved as: {output_file}")
    
    return output_file, df_10y

if __name__ == "__main__":
    print("=== COMPLETE BANRESERVAS DATA EXTRACTION ===")
    print("Extracting ALL available data from cached files\n")
    
    # Extract all data
    df = extract_all_banreservas_data()
    
    if not df.empty:
        # Save complete dataset
        df.to_csv('banreservas_complete_historical_data.csv', index=False)
        print(f"Complete dataset saved to: banreservas_complete_historical_data.csv")
        
        # Create 10-year analysis
        result = create_complete_10year_analysis(df)
        
        if result:
            output_file, df_10y = result
            
            print(f"\n✅ SUCCESS: Complete analysis generated")
            print(f"📈 Chart: {output_file}")
            print(f"📊 10-year data: {len(df_10y)} monthly observations")
            print(f"🏦 CB data coverage: {(df_10y['banco_central_asset'] > 0).sum()} actual + {(df_10y['banco_central_asset'] == 0).sum()} estimated")
            print(f"🏛️ Government deposits range: {df_10y['government_deposits'].min()/1e9:.1f}B - {df_10y['government_deposits'].max()/1e9:.1f}B DOP")
            
            # Show sample data
            print(f"\n=== SAMPLE RECENT DATA ===")
            recent = df_10y.tail(6)
            for _, row in recent.iterrows():
                method = "📊" if row['banco_central_asset'] > 0 else "🔢"
                print(f"{method} {row['date'].strftime('%Y-%m')}: "
                      f"CB: {row['realistic_cb_liquidity']/1e9:.1f}B, "
                      f"Gov: {row['government_deposits']/1e9:.1f}B, "
                      f"Share: {row['gov_share_pct']:.1f}%")
        
    else:
        print("❌ No data extracted")