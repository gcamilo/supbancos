#!/usr/bin/env python3

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

def extract_comprehensive_banreservas_data():
    """
    Extract comprehensive Banreservas data from all cached EIF files.
    Focus on central bank liquidity (1.a.2) and government deposits analysis.
    """
    cache_dir = 'cache'
    cache_files = [f for f in os.listdir(cache_dir) if f.startswith('eif_') and f.endswith('.json')]
    
    print(f"Found {len(cache_files)} cached EIF files")
    print("Extracting comprehensive Banreservas data...")
    
    results = []
    missing_periods = []
    
    # Load government deposits data if available
    gov_deposits_data = {}
    try:
        gov_df = pd.read_csv('banreservas_government_deposits_data.csv')
        gov_df['Date'] = pd.to_datetime(gov_df['Date'])
        gov_df['period'] = gov_df['Date'].dt.strftime('%Y-%m')
        for _, row in gov_df.iterrows():
            gov_deposits_data[row['period']] = {
                'government_deposits': row['GovernmentDeposits'] * 1e6,  # Convert to DOP
                'government_share': row['GovernmentShare']
            }
        print(f"Loaded government deposit data for {len(gov_deposits_data)} periods")
    except FileNotFoundError:
        print("Government deposits file not found - continuing without it")
    
    for cache_file in sorted(cache_files):
        period = cache_file.replace('eif_', '').replace('.json', '')
        
        try:
            with open(os.path.join(cache_dir, cache_file), 'r') as f:
                data = json.load(f)
            
            # Find Banreservas records
            banreservas_data = [d for d in data if d.get('entidad') == 'BANRESERVAS']
            
            if not banreservas_data:
                missing_periods.append(period)
                continue
            
            # Initialize all balance sheet components
            balance_sheet = {
                # Assets - Cash and Equivalents
                'banco_central_asset': 0,      # 1.a.2 - The specific line item requested
                'caja': 0,                     # Cash on hand
                'bancos_pais': 0,              # Domestic banks
                'bancos_exterior': 0,          # Foreign banks
                'equivalentes_efectivo': 0,    # Cash equivalents
                'total_efectivo_todos': 0,     # Total cash (when reported as aggregate)
                
                # Liabilities - Deposits
                'depositos_publico_total': 0,  # Total public deposits
                'depositos_vista': 0,          # Demand deposits
                'depositos_ahorro': 0,         # Savings deposits  
                'depositos_plazo': 0,          # Time deposits
                'depositos_otros': 0,          # Other deposits
                
                # Central Bank Liabilities
                'banco_central_liability': 0,  # Borrowings from central bank
                
                # Other key items
                'total_activos': 0,            # Total assets
                'total_pasivos': 0,            # Total liabilities
                'patrimonio': 0                # Capital
            }
            
            # Process all Banreservas records for this period
            for record in banreservas_data:
                concept1 = record.get('conceptoNivel1', '')
                concept2 = record.get('conceptoNivel2', '')
                concept3 = record.get('conceptoNivel3', '')
                valor = record.get('valor', 0)
                
                # Assets: Cash and Cash Equivalents
                if concept1 == 'Activos' and concept2 == 'Efectivo y equivalentes de efectivo':
                    if concept3 == 'Banco central':
                        balance_sheet['banco_central_asset'] = valor  # This is 1.a.2
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
                
                # Total Assets and Liabilities
                if concept1 == 'Activos' and concept2 == 'TODOS':
                    balance_sheet['total_activos'] = valor
                elif concept1 == 'Pasivos' and concept2 == 'TODOS':
                    balance_sheet['total_pasivos'] = valor
                elif concept1 == 'Patrimonio' and concept2 == 'TODOS':
                    balance_sheet['patrimonio'] = valor
                
                # Liabilities: Deposits from Public
                if concept1 == 'Pasivos' and 'Depósitos del público' in concept2:
                    if concept3 == 'TODOS' or concept2 == 'Depósitos del público':
                        balance_sheet['depositos_publico_total'] += valor
                    elif 'vista' in concept3.lower():
                        balance_sheet['depositos_vista'] = valor
                    elif 'ahorro' in concept3.lower():
                        balance_sheet['depositos_ahorro'] = valor
                    elif 'plazo' in concept3.lower():
                        balance_sheet['depositos_plazo'] = valor
                    else:
                        balance_sheet['depositos_otros'] += valor
                
                # Central Bank Liabilities (borrowings)
                if concept1 == 'Pasivos' and 'Fondos tomados a préstamo' in concept2:
                    if 'central' in concept3.lower() or 'Central' in concept3:
                        balance_sheet['banco_central_liability'] = valor
            
            # Calculate derived metrics
            total_liquid_assets = balance_sheet['total_efectivo_todos'] if balance_sheet['total_efectivo_todos'] > 0 else (
                balance_sheet['banco_central_asset'] + balance_sheet['caja'] + 
                balance_sheet['bancos_pais'] + balance_sheet['bancos_exterior'] + 
                balance_sheet['equivalentes_efectivo']
            )
            
            # Net central bank position
            net_cb_position = balance_sheet['banco_central_asset'] - balance_sheet['banco_central_liability']
            
            # Get government deposits for this period
            gov_data = gov_deposits_data.get(period, {'government_deposits': 0, 'government_share': 0})
            
            # Calculate ratios
            total_deposits = balance_sheet['depositos_publico_total']
            cb_to_deposits_ratio = (balance_sheet['banco_central_asset'] / total_deposits * 100) if total_deposits > 0 else 0
            liquid_to_deposits_ratio = (total_liquid_assets / total_deposits * 100) if total_deposits > 0 else 0
            
            # Create final record
            record_data = {
                'period': period,
                'date': datetime.strptime(period + '-01', '%Y-%m-%d'),
                
                # Central Bank Assets (1.a.2) - The key metric requested
                'banco_central_asset_1a2': balance_sheet['banco_central_asset'],
                'banco_central_liability': balance_sheet['banco_central_liability'],
                'net_cb_position': net_cb_position,
                
                # Cash Components
                'caja': balance_sheet['caja'],
                'bancos_pais': balance_sheet['bancos_pais'],
                'bancos_exterior': balance_sheet['bancos_exterior'],
                'equivalentes_efectivo': balance_sheet['equivalentes_efectivo'],
                'total_liquid_assets': total_liquid_assets,
                
                # Deposits
                'total_deposits': total_deposits,
                'depositos_vista': balance_sheet['depositos_vista'],
                'depositos_ahorro': balance_sheet['depositos_ahorro'],
                'depositos_plazo': balance_sheet['depositos_plazo'],
                
                # Government Deposits
                'government_deposits': gov_data['government_deposits'],
                'government_share_pct': gov_data['government_share'],
                
                # Balance Sheet Totals
                'total_activos': balance_sheet['total_activos'],
                'total_pasivos': balance_sheet['total_pasivos'],
                'patrimonio': balance_sheet['patrimonio'],
                
                # Key Ratios
                'cb_to_deposits_ratio': cb_to_deposits_ratio,
                'liquid_to_deposits_ratio': liquid_to_deposits_ratio,
                
                # Data Quality
                'has_cb_asset_data': balance_sheet['banco_central_asset'] > 0,
                'has_total_deposits': total_deposits > 0,
                'data_completeness': 'complete' if (balance_sheet['banco_central_asset'] > 0 and total_deposits > 0) else 'partial'
            }
            
            results.append(record_data)
                
        except Exception as e:
            print(f"Error processing {cache_file}: {e}")
            missing_periods.append(period)
    
    print(f"\nData extraction complete:")
    print(f"  Successfully processed: {len(results)} periods")
    print(f"  Missing/failed periods: {len(missing_periods)}")
    
    # Create DataFrame
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('date')
        
        # Data quality summary
        complete_data = df[df['data_completeness'] == 'complete']
        cb_data_available = df[df['has_cb_asset_data'] == True]
        
        print(f"\nData Quality Summary:")
        print(f"  Complete records (CB + deposits): {len(complete_data)}")
        print(f"  Records with CB asset data (1.a.2): {len(cb_data_available)}")
        print(f"  Coverage period: {df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}")
        
        if len(cb_data_available) > 0:
            cb_stats = cb_data_available['banco_central_asset_1a2'] / 1e9
            print(f"\nCentral Bank Asset (1.a.2) Statistics (Billion DOP):")
            print(f"  Count: {len(cb_data_available)} observations")
            print(f"  Mean: {cb_stats.mean():.1f}")
            print(f"  Median: {cb_stats.median():.1f}")
            print(f"  Min: {cb_stats.min():.1f}")
            print(f"  Max: {cb_stats.max():.1f}")
    
    return df

def create_comprehensive_analysis_chart(df):
    """
    Create comprehensive 4-panel analysis of Banreservas data.
    """
    if df.empty:
        print("No data available for charting")
        return None
    
    # Filter to periods with meaningful data
    df_analysis = df[df['data_completeness'] == 'complete'].copy()
    
    if df_analysis.empty:
        print("No complete data records for analysis")
        return None
    
    print(f"Creating comprehensive analysis with {len(df_analysis)} complete records")
    
    # Create the visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # Panel 1: Central Bank Asset (1.a.2) Historical Trend
    cb_data = df_analysis[df_analysis['banco_central_asset_1a2'] > 0]
    if not cb_data.empty:
        ax1.plot(cb_data['date'], cb_data['banco_central_asset_1a2'] / 1e9, 
                'bo-', linewidth=2, markersize=4, alpha=0.8, label='Banco Central Asset (1.a.2)')
        
        # Add trend line
        x_numeric = np.arange(len(cb_data))
        z = np.polyfit(x_numeric, cb_data['banco_central_asset_1a2'] / 1e9, 1)
        p = np.poly1d(z)
        ax1.plot(cb_data['date'], p(x_numeric), 'r--', alpha=0.6, linewidth=2, label='Trend')
    
    ax1.set_title('Banreservas: Central Bank Asset Holdings (1.a.2)\nEfectivo y equivalentes de efectivo → Banco central', 
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('CB Assets (Billion DOP)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: CB Assets vs Government Deposits
    gov_data = df_analysis[df_analysis['government_deposits'] > 0]
    cb_and_gov = df_analysis[(df_analysis['banco_central_asset_1a2'] > 0) & 
                            (df_analysis['government_deposits'] > 0)]
    
    if not cb_and_gov.empty:
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(cb_and_gov['date'], cb_and_gov['banco_central_asset_1a2'] / 1e9, 
                        'b-', linewidth=2, alpha=0.8, label='CB Assets (1.a.2)')
        line2 = ax2_twin.plot(cb_and_gov['date'], cb_and_gov['government_deposits'] / 1e9, 
                             'r-', linewidth=2, alpha=0.8, label='Gov Deposits')
        
        ax2.set_ylabel('CB Assets (Billion DOP)', color='b', fontsize=12)
        ax2_twin.set_ylabel('Gov Deposits (Billion DOP)', color='r', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='b')
        ax2_twin.tick_params(axis='y', labelcolor='r')
        
        # Calculate correlation
        correlation = cb_and_gov['banco_central_asset_1a2'].corr(cb_and_gov['government_deposits'])
        ax2.text(0.02, 0.98, f'Correlation: {correlation:.3f}', transform=ax2.transAxes, 
                fontsize=11, bbox=dict(boxstyle="round,pad=0.3", facecolor='wheat', alpha=0.8),
                verticalalignment='top')
    
    ax2.set_title('Central Bank Assets vs Government Deposits\n(Monthly Relationship)', 
                  fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Liquidity Ratios
    ratio_data = df_analysis[df_analysis['cb_to_deposits_ratio'] > 0]
    if not ratio_data.empty:
        ax3.plot(ratio_data['date'], ratio_data['cb_to_deposits_ratio'], 
                'g-', linewidth=2, marker='o', markersize=3, alpha=0.8, label='CB/Deposits Ratio')
        ax3.plot(ratio_data['date'], ratio_data['liquid_to_deposits_ratio'], 
                'orange', linewidth=2, marker='s', markersize=2, alpha=0.7, label='Total Liquid/Deposits')
        
        # Add reference lines
        ax3.axhline(y=10, color='red', linestyle='--', alpha=0.5, label='10% Reference')
        ax3.axhline(y=20, color='purple', linestyle='--', alpha=0.5, label='20% Reference')
    
    ax3.set_title('Banreservas: Liquidity Ratios\n(CB Assets and Total Liquid Assets as % of Deposits)', 
                  fontsize=14, fontweight='bold')
    ax3.set_ylabel('Ratio (%)', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Balance Sheet Components (Recent Period)
    recent_data = df_analysis.tail(24)  # Last 24 months
    if not recent_data.empty:
        ax4.fill_between(recent_data['date'], 0, recent_data['caja'] / 1e9, 
                        alpha=0.7, label='Cash on Hand', color='gold')
        ax4.fill_between(recent_data['date'], recent_data['caja'] / 1e9, 
                        (recent_data['caja'] + recent_data['bancos_exterior']) / 1e9, 
                        alpha=0.7, label='Foreign Banks', color='orange')
        ax4.fill_between(recent_data['date'], 
                        (recent_data['caja'] + recent_data['bancos_exterior']) / 1e9,
                        (recent_data['caja'] + recent_data['bancos_exterior'] + 
                         recent_data['banco_central_asset_1a2']) / 1e9,
                        alpha=0.7, label='CB Assets (1.a.2)', color='blue')
    
    ax4.set_title('Liquidity Components Breakdown\n(Last 24 Months)', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Amount (Billion DOP)', fontsize=12)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Format all x-axes
    for ax in [ax1, ax2, ax3, ax4]:
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Save chart
    output_file = 'banreservas_comprehensive_monthly_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nComprehensive analysis chart saved as: {output_file}")
    
    return output_file

if __name__ == "__main__":
    print("=== COMPREHENSIVE BANRESERVAS ANALYSIS ===")
    print("Extracting data from cached EIF files (2005-2025)")
    print("Focus: Central Bank Asset (1.a.2) and Government Deposits\n")
    
    # Extract comprehensive data
    df = extract_comprehensive_banreservas_data()
    
    if not df.empty:
        # Save the comprehensive dataset
        output_csv = 'banreservas_comprehensive_monthly_data.csv'
        df.to_csv(output_csv, index=False)
        print(f"\nComprehensive dataset saved to: {output_csv}")
        
        # Create comprehensive analysis chart
        create_comprehensive_analysis_chart(df)
        
        # Show recent data summary
        print(f"\n=== RECENT DATA SUMMARY (Last 12 months) ===")
        recent = df.tail(12)
        for _, row in recent.iterrows():
            cb_status = "✅" if row['banco_central_asset_1a2'] > 0 else "❌"
            gov_status = "🏛️" if row['government_deposits'] > 0 else "⚪"
            print(f"{cb_status}{gov_status} {row['date'].strftime('%Y-%m')}: "
                  f"CB Asset (1.a.2): {row['banco_central_asset_1a2']/1e9:.1f}B DOP, "
                  f"Gov Deposits: {row['government_deposits']/1e9:.1f}B DOP, "
                  f"CB Ratio: {row['cb_to_deposits_ratio']:.1f}%")
        
        print(f"\n✅ COMPLETE: Comprehensive monthly analysis of Banreservas")
        print(f"📊 Data coverage: {len(df)} periods total")
        print(f"🏦 CB Asset data: {df['has_cb_asset_data'].sum()} periods with 1.a.2 data")
        print(f"🏛️ Government deposits: {(df['government_deposits'] > 0).sum()} periods")
        
    else:
        print("❌ No data could be extracted from cache files")