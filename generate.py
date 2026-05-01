"""
Newsletter Generator for ausyield.com.au
Generates complete HTML newsletter from scraped data + commentary

Usage:
    python generate_newsletter.py [--month YYYY-MM] [--preview]

Inputs:
    - fund_config.xlsx: Fund names, asset classes, benchmark flags
    - fund_performance_YYYYMMDD.csv: Scraped performance data (latest file used)
    - commentary.md: Your written commentary for each section

Outputs:
    - newsletter_YYYY_MM.html: Complete newsletter ready for upload
"""

import pandas as pd
import json
import re
import os
import glob
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import webbrowser
import markdown

# =============================================================================
# CONFIGURATION
# =============================================================================

ASSET_CLASS_CONFIG = {
    'Fixed Income': {
        'table_id': 'fixedIncome',
        'columns': ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa'],
        'has_cpi_headers': True,
        'benchmark_label': 'Benchmark'
    },
    'Private Credit': {
        'table_id': 'privateCredit', 
        'columns': ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa'],
        'has_cpi_headers': False,
        'benchmark_label': 'Benchmark'
    },
    'Domestic Large Cap': {
        'table_id': 'domesticLargeCap',
        'columns': ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa'],
        'has_cpi_headers': False,
        'show_outperformance': True,
        'benchmark_label': 'Benchmark'
    },
    'Domestic Mid/Small Cap': {
        'table_id': 'domesticMidSmallCap',
        'columns': ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa'],
        'has_cpi_headers': False,
        'show_outperformance': True,
        'show_dual_benchmark': True,
        'benchmark_label': 'Benchmark'
    },
    'Domestic Micro Cap': {
        'table_id': 'domesticMicroCap',
        'columns': ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa'],
        'has_cpi_headers': False,
        'show_outperformance': True,
        'benchmark_label': 'Benchmark'
    },
    'International Equities': {
        'table_id': 'internationalEquities',
        'columns': ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa'],
        'has_cpi_headers': False,
        'show_outperformance': True,
        'benchmark_label': 'Benchmark'
    },
    'Infra + REITs': {
        'table_id': 'infraReits',
        'columns': ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa'],
        'has_cpi_headers': False,
        'benchmark_label': None  # No benchmark legend
    },
    'Other': {
        'table_id': 'other',
        'columns': ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa'],
        'has_cpi_headers': False,
        'show_outperformance': True,
        'benchmark_label': 'Benchmark (Spot Gold)'
    },
    'GICS Sectors': {
        'table_id': 'gicsSectors',
        'columns': ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa', '5 Yr pa', '10 Yr pa'],
        'has_cpi_headers': False,
        'show_outperformance': True,
        'benchmark_label': 'Benchmark'
    },
    'Crypto': {
        'table_id': 'crypto',
        'columns': ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa'],
        'has_cpi_headers': False,
        'benchmark_label': None
    }
}

# Column mapping from scraped CSV to display
COLUMN_MAP = {
    '1M': '1 Mth',
    '3M': '3 Mth', 
    '1Y p.a.': '1 Yr pa',
    '3Y p.a.': '3 Yr pa',
    '5Y p.a.': '5 Yr pa',
    '10Y p.a.': '10 Yr pa'
}

# =============================================================================
# DATA LOADING
# =============================================================================

def load_fund_config(config_path='fund_config.xlsx'):
    """Load fund configuration from Excel"""
    df = pd.read_excel(config_path)
    
    # Filter out inactive funds if Active column exists
    if 'Active' in df.columns:
        before_count = len(df)
        # Keep rows where Active is True, 'TRUE', 'Yes', 1, or missing (default to active)
        df['Active'] = df['Active'].fillna(True)
        df = df[df['Active'].astype(str).str.lower().isin(['true', 'yes', '1', '1.0'])]
        filtered = before_count - len(df)
        if filtered > 0:
            print(f"Filtered out {filtered} inactive funds")
    
    return df

def load_performance_data(data_path=None):
    """Load most recent performance CSV if no path specified"""
    if data_path is None:
        # Find most recent fund_performance CSV
        csvs = glob.glob('fund_performance_*.csv')
        if not csvs:
            raise FileNotFoundError("No fund_performance_*.csv files found")
        data_path = max(csvs, key=os.path.getmtime)
        print(f"Using performance data: {data_path}")
    
    df = pd.read_csv(data_path)
    return df

def load_benchmark_data(benchmark_path='benchmark_data.csv'):
    """Load auto-fetched benchmark data (Gold, Silver, BTC, ETH)"""
    if not os.path.exists(benchmark_path):
        print(f"Note: {benchmark_path} not found. Run fetch_benchmarks.py first.")
        return pd.DataFrame()
    
    df = pd.read_csv(benchmark_path)
    print(f"Loaded {len(df)} benchmarks from {benchmark_path}")
    return df

def load_manual_data(manual_path='manual_data.xlsx'):
    """Load manual data (CPI, GICS sectors, fallbacks)"""
    if not os.path.exists(manual_path):
        print(f"Note: {manual_path} not found.")
        return pd.DataFrame()
    
    dfs = []
    
    # Load CPI benchmarks
    try:
        df_cpi = pd.read_excel(manual_path, sheet_name='CPI_Benchmarks')
        df_cpi = df_cpi[df_cpi['Fund Name'].notna()]
        dfs.append(df_cpi)
        print(f"Loaded {len(df_cpi)} CPI benchmarks")
    except Exception as e:
        print(f"Warning: Could not load CPI_Benchmarks: {e}")
    
    # Load GICS sectors
    try:
        df_gics = pd.read_excel(manual_path, sheet_name='GICS_Sectors')
        df_gics = df_gics[df_gics['Fund Name'].notna()]
        # Only include rows with actual data
        df_gics = df_gics[df_gics['1 Mth'].notna()]
        dfs.append(df_gics)
        print(f"Loaded {len(df_gics)} GICS sectors")
    except Exception as e:
        print(f"Warning: Could not load GICS_Sectors: {e}")
    
    # Load other manual entries (fallbacks)
    try:
        df_other = pd.read_excel(manual_path, sheet_name='Other_Manual')
        df_other = df_other[df_other['Fund Name'].notna()]
        df_other = df_other[df_other['1 Mth'].notna()]
        if len(df_other) > 0:
            dfs.append(df_other)
            print(f"Loaded {len(df_other)} other manual entries")
    except Exception as e:
        pass  # This sheet may be empty, that's fine
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def load_commentary(commentary_path='commentary.md'):
    """Load and parse commentary markdown"""
    if not os.path.exists(commentary_path):
        print(f"Warning: {commentary_path} not found. Using empty commentary.")
        return {}

    with open(commentary_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse sections
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        # Check for ## headers (asset class sections)
        if line.startswith('## ') and not line.startswith('### '):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)
    
    # Don't forget last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def parse_percentage(val):
    """Convert percentage string to float"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if pd.isna(val):
            return None
        return float(val)
    if not isinstance(val, str):
        return None
    val = str(val).replace('%', '').replace(',', '').strip()
    if val in ['-', '-%', '', 'nan', 'None']:
        return None
    try:
        return float(val)
    except ValueError:
        return None

# =============================================================================
# DATA PROCESSING
# =============================================================================

def merge_data(config_df, perf_df):
    """Merge config with performance data"""
    # Clean performance data column names
    perf_df = perf_df.copy()
    perf_df = perf_df.rename(columns=COLUMN_MAP)
    
    # Parse percentage columns
    perf_cols = ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa', '5 Yr pa', '10 Yr pa']
    for col in perf_cols:
        if col in perf_df.columns:
            perf_df[col] = perf_df[col].apply(parse_percentage)
    
    # Ensure all required columns exist
    for col in perf_cols:
        if col not in perf_df.columns:
            perf_df[col] = None
    
    # Merge on fund name
    merge_cols = ['Fund Name'] + [c for c in perf_cols if c in perf_df.columns]
    merged = config_df.merge(
        perf_df[merge_cols],
        on='Fund Name',
        how='left'
    )
    
    return merged

def calculate_outperformance(data, benchmark_col='1 Yr pa', benchmark_name=None, columns=None):
    """Calculate % of funds outperforming benchmark"""
    if columns is None:
        columns = ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa']
    
    if benchmark_name is None:
        benchmarks = data[data['Is Benchmark'] == True]
        if len(benchmarks) == 0:
            return {}
        benchmark_val = benchmarks.iloc[0][benchmark_col]
    else:
        bm = data[data['Fund Name'] == benchmark_name]
        if len(bm) == 0:
            return {}
        benchmark_val = bm.iloc[0][benchmark_col]
    
    if pd.isna(benchmark_val):
        return {}
    
    non_bm = data[data['Is Benchmark'] == False]
    results = {}
    
    for col in columns:
        if col not in data.columns:
            continue
        valid = non_bm[col].dropna()
        if len(valid) == 0:
            results[col] = None
            continue
        bm_val = data[data['Is Benchmark'] == True][col].iloc[0] if len(data[data['Is Benchmark'] == True]) > 0 else None
        if bm_val is None or pd.isna(bm_val):
            results[col] = None
            continue
        outperformed = (valid > bm_val).sum()
        results[col] = f"{outperformed / len(valid) * 100:.1f}%"
    
    return results


def calculate_cpi_outperformance(data, cpi_data):
    """Calculate % of funds outperforming CPI, CPI+1%, CPI+2%, CPI+3%"""
    results = {
        'CPI': {},
        'CPI+1%': {},
        'CPI+2%': {},
        'CPI+3%': {}
    }
    
    cpi_map = {
        'CPI': 'Australian CPI (non-seasonal adj)',
        'CPI+1%': 'Australian CPI+1% (non-seasonal adj)',
        'CPI+2%': 'Australian CPI+2% (non-seasonal adj)',
        'CPI+3%': 'Australian CPI+3% (non-seasonal adj)'
    }
    
    # Get non-benchmark funds
    non_bm = data[data['Is Benchmark'] != True]
    
    for cpi_label, cpi_name in cpi_map.items():
        cpi_row = cpi_data[cpi_data['Fund Name'] == cpi_name]
        if len(cpi_row) == 0:
            continue
        
        for col in ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa']:
            if col not in data.columns or col not in cpi_row.columns:
                continue
            
            cpi_val = cpi_row.iloc[0][col]
            if pd.isna(cpi_val):
                results[cpi_label][col] = '--'
                continue
            
            valid = non_bm[col].dropna()
            if len(valid) == 0:
                results[cpi_label][col] = '--'
                continue
            
            outperformed = (valid > cpi_val).sum()
            results[cpi_label][col] = f"{outperformed / len(valid) * 100:.1f}%"
    
    return results

# =============================================================================
# HTML GENERATION
# =============================================================================

def commentary_to_html(md_content):
    """Convert markdown commentary to HTML"""
    if not md_content or md_content.startswith('[Your'):
        return ''
    
    # Convert markdown to HTML
    html = markdown.markdown(md_content)
    return html

def generate_table_data_js(asset_class, data, config):
    """Generate JavaScript data array for a table"""
    columns = config['columns']
    
    # Sort by 1 Mth (default sort)
    data = data.sort_values('1 Mth', ascending=False, na_position='last')
    
    rows = []
    for _, row in data.iterrows():
        values = []
        for col in columns:
            val = row.get(col)
            if pd.isna(val):
                values.append('null')
            else:
                values.append(f"{val:.2f}")
        
        is_benchmark = 'true' if row.get('Is Benchmark', False) else 'false'
        # Use Display Name if available, otherwise fall back to Fund Name
        display_name = row.get('Display Name')
        if pd.isna(display_name) or not display_name:
            display_name = row['Fund Name']
        name = str(display_name).replace("'", "\\'")
        rows.append(f"            {{ name: '{name}', values: [{', '.join(values)}], isBenchmark: {is_benchmark} }}")
    
    return ',\n'.join(rows)

def generate_table_html(asset_class, config, commentary_html, outperformance=None, cpi_outperformance=None):
    """Generate HTML for a single asset class table"""
    table_id = config['table_id']
    columns = config['columns']
    
    # Build fixed header rows if needed
    fixed_headers = ''
    if config.get('has_cpi_headers') and cpi_outperformance:
        cpi_rows = []
        for cpi_label in ['CPI', 'CPI+1%', 'CPI+2%', 'CPI+3%']:
            cpi_vals = cpi_outperformance.get(cpi_label, {})
            vals = [cpi_vals.get(col, '--') or '--' for col in columns]
            cpi_rows.append(f'''                <tr><td>% of funds that outperformed {cpi_label}</td>{''.join(f'<td>{v}</td>' for v in vals)}</tr>''')
        fixed_headers = '\n'.join(cpi_rows)
    elif config.get('has_cpi_headers'):
        # Fallback to -- if no CPI data
        fixed_headers = '''
                <tr><td>% of funds that outperformed CPI</td><td>--</td><td>--</td><td>--</td><td>--</td></tr>
                <tr><td>% of funds that outperformed CPI+1%</td><td>--</td><td>--</td><td>--</td><td>--</td></tr>
                <tr><td>% of funds that outperformed CPI+2%</td><td>--</td><td>--</td><td>--</td><td>--</td></tr>
                <tr><td>% of funds that outperformed CPI+3%</td><td>--</td><td>--</td><td>--</td><td>--</td></tr>'''
    elif config.get('show_outperformance') and outperformance:
        vals = [outperformance.get(col, '--') or '--' for col in columns]
        fixed_headers = f'''
                <tr><td>% of funds that outperformed benchmark</td>{''.join(f'<td>{v}</td>' for v in vals)}</tr>'''
    
    # Build column headers
    col_headers = []
    for i, col in enumerate(columns):
        col_headers.append(f'''<th onclick="handleSort('{table_id}', {i})"><div class="sort-header"><span>{col}</span></div></th>''')
    
    # Legend
    benchmark_label = config.get('benchmark_label')
    legend_benchmark = f'<span class="legend-item"><span class="legend-color benchmark"></span> {benchmark_label}</span>' if benchmark_label else ''

    # Add gics-wide class for GICS Sectors table
    table_class = 'table-container gics-wide' if asset_class == 'GICS Sectors' else 'table-container'

    html = f'''
<h2>{asset_class}</h2>

{commentary_html}

<div class="{table_class}">
    <div class="table-overflow">
        <table id="{table_id}Table">
            <thead>{fixed_headers}
                <tr class="column-header">
                    <th>{asset_class}</th>
                    {chr(10).join(f'                    {h}' for h in col_headers)}
                </tr>
            </thead>
            <tbody id="{table_id}Body"></tbody>
        </table>
    </div>
</div>

<div class="table-legend">
    <div class="legend-items">
        <span class="legend-item"><span class="legend-color max"></span> Best performer</span>
        <span class="legend-item"><span class="legend-color min"></span> Worst performer</span>
        {legend_benchmark}
    </div>
</div>
'''
    return html

def generate_full_html(merged_data, commentary, month_str, manual_path='manual_data.xlsx'):
    """Generate complete newsletter HTML"""
    
    # Parse month for title
    try:
        dt = datetime.strptime(month_str, '%Y-%m')
        month_display = dt.strftime('%B %Y')
    except:
        month_display = month_str
    
    # Generate table sections and JS data
    table_sections = []
    js_table_configs = []
    
    # Load CPI data separately for Fixed Income outperformance calculation
    cpi_data = None
    try:
        cpi_data = pd.read_excel(manual_path, sheet_name='CPI_Benchmarks')
        cpi_data = cpi_data[cpi_data['Fund Name'].notna()]
    except Exception as e:
        print(f"Warning: Could not load CPI data for outperformance: {e}")
    
    for asset_class, config in ASSET_CLASS_CONFIG.items():
        # Get data for this asset class
        ac_data = merged_data[merged_data['Asset Class'] == asset_class].copy()
        
        # Filter 1: Only include Active funds (if column exists)
        if 'Active' in ac_data.columns:
            ac_data = ac_data[ac_data['Active'] != False]
        
        # Auto-inject CPI rows into Fixed Income
        if asset_class == 'Fixed Income' and cpi_data is not None and len(cpi_data) > 0:
            cpi_rows = cpi_data.copy()
            cpi_rows['Asset Class'] = 'Fixed Income'
            cpi_rows['Is Benchmark'] = True
            # Ensure all required columns exist
            for col in ac_data.columns:
                if col not in cpi_rows.columns:
                    cpi_rows[col] = None
            ac_data = pd.concat([ac_data, cpi_rows[ac_data.columns]], ignore_index=True)
            print(f"Added {len(cpi_rows)} CPI benchmarks to Fixed Income")
        
        # Filter 2: Only include funds with actual data (1 Mth not blank)
        ac_data = ac_data[ac_data['1 Mth'].notna()]
        
        if len(ac_data) == 0:
            print(f"Warning: No data for {asset_class}")
            continue
        
        # Get commentary
        commentary_html = commentary_to_html(commentary.get(asset_class, ''))
        
        # Calculate outperformance if needed
        outperformance = None
        cpi_outperformance = None
        
        if config.get('has_cpi_headers') and cpi_data is not None:
            # Calculate CPI outperformance for Fixed Income
            cpi_outperformance = calculate_cpi_outperformance(ac_data, cpi_data)
        elif config.get('show_outperformance'):
            # Pass the columns from config so GICS gets 5yr and 10yr
            outperformance = calculate_outperformance(ac_data, columns=config['columns'])
        
        # Generate HTML section
        table_html = generate_table_html(asset_class, config, commentary_html, outperformance, cpi_outperformance)
        table_sections.append(table_html)
        
        # Generate JS config
        table_id = config['table_id']
        has_fixed = 'true' if config.get('has_cpi_headers') or config.get('show_outperformance') else 'false'
        js_data = generate_table_data_js(asset_class, ac_data, config)
        
        js_table_configs.append(f'''    {table_id}: {{
        tableId: '{table_id}Table',
        bodyId: '{table_id}Body',
        hasFixedHeaders: {has_fixed},
        data: [
{js_data}
        ]
    }}''')
    
    # Get Thought of the Month
    thought_html = ''
    if 'Thought of the Month' in commentary:
        thought_content = commentary['Thought of the Month']
        if thought_content and not thought_content.startswith('[Your'):
            thought_html = f'''
<h2 class="essay-title">Thought of the Month</h2>

{markdown.markdown(thought_content)}
'''
    
    # Get Thanks section
    thanks_html = ''
    if 'Thanks' in commentary:
        thanks_content = commentary['Thanks']
        if thanks_content:
            thanks_html = f'''
<h2>Thanks</h2>

{markdown.markdown(thanks_content)}
'''
    
    # Assemble full HTML
    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monthly Market Update - {month_display}</title>
    <meta name="description" content="{month_display} Monthly Market Commentary and Fund Rankings">
    <style type="text/css">
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
            line-height: 1.6;
            color: #111;
            background-color: #fffff8;
            display: flex;
            flex-direction: column;
            max-width: 55em;
            margin: 0 auto;
            padding: 1.5em 1em;
        }}

        header {{
            width: 100%;
            padding-bottom: 1.5em;
            border-bottom: 1px solid #eee;
            margin-bottom: 1.5em;
        }}

        main {{
            flex: 1;
            max-width: 50em;
        }}

        nav {{
            display: flex;
            flex-direction: row;
            gap: 2em;
        }}

        nav a {{
            margin-bottom: 0.5em;
            font-size: 0.9em;
            color: #0066cc;
            text-decoration: none;
        }}

        nav a:hover {{
            text-decoration: underline;
        }}

        h1, h2, h3 {{
            font-weight: normal;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}

        h1 {{
            font-size: 1.8em;
        }}

        h2 {{
            font-size: 1.4em;
        }}

        h2.essay-title {{
            font-weight: bold;
            margin-top: 2.5em;
            border-top: 1px solid #ddd;
            padding-top: 1.5em;
        }}

        h3 {{
            font-size: 1.2em;
        }}

        p, ul {{
            margin-bottom: 1.2em;
        }}

        ul {{
            padding-left: 1.2em;
        }}

        li {{
            margin-bottom: 0.25em;
        }}

        li > ul {{
            margin-top: 0.25em;
            margin-bottom: 0.25em;
        }}

        .image-container {{
            margin: 1.5em 0;
            text-align: center;
        }}

        .image-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 0;
            display: inline-block;
        }}

        .image-container img.standard {{
            max-width: 600px;
            height: auto;
        }}

        /* TABLE STYLES */
        .table-container {{
            background: white;
            border: 1px solid #e5e7eb;
            margin: 1.5em 0;
            width: 100%;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}

        .table-overflow {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            position: relative;
        }}

        /* Mobile scroll shadow indicator */
        @media (max-width: 767px) {{
            .table-overflow {{
                background:
                    linear-gradient(to right, white 30%, rgba(255,255,255,0)),
                    linear-gradient(to right, rgba(255,255,255,0), white 70%) 100% 0,
                    linear-gradient(to right, rgba(0,0,0,0.1), rgba(0,0,0,0)),
                    linear-gradient(to left, rgba(0,0,0,0.1), rgba(0,0,0,0)) 100% 0;
                background-repeat: no-repeat;
                background-size: 40px 100%, 40px 100%, 14px 100%, 14px 100%;
                background-attachment: local, local, scroll, scroll;
            }}
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
        }}

        @media (max-width: 767px) {{
            table {{
                font-size: 10px;
            }}

            thead tr:not(.column-header) td,
            thead tr:not(.column-header) th,
            tbody td,
            tbody th {{
                padding: 0.1rem 0.5rem !important;
            }}

            /* Truncate fund names on mobile */
            tbody td:first-child {{
                max-width: 140px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
        }}

        thead tr:not(.column-header) {{
            background-color: #f3f4f6;
            border-bottom: 1px solid #d1d5db;
        }}

        thead tr:not(.column-header) td {{
            padding: 0.2rem 1rem;
            font-weight: normal;
            color: #111;
            text-align: right;
            border-right: 1px solid #d1d5db;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        thead tr:not(.column-header) td:first-child {{
            text-align: left;
        }}

        thead tr:not(.column-header) td:last-child {{
            border-right: none;
        }}

        .column-header {{
            background-color: #2c3e50;
            color: white;
            position: sticky;
            top: 0;
            z-index: 20;
        }}

        .column-header th {{
            padding: 0.35rem 1rem;
            text-align: right;
            font-weight: 600;
            border-right: 1px solid #1a252f;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
            transition: background-color 0.2s ease;
            min-width: 5.5em;
        }}

        .column-header th:first-child {{
            text-align: left;
            cursor: default;
        }}

        .column-header th:last-child {{
            border-right: none;
        }}

        .column-header th:hover:not(:first-child) {{
            background-color: #1a252f;
        }}

        .sort-header {{
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.25rem;
            position: relative;
            padding-right: 14px;
        }}

        .chevron {{
            width: 10px;
            height: 10px;
            display: inline-block;
            flex-shrink: 0;
            position: absolute;
            right: 0;
        }}

        tbody tr {{
            border-bottom: 1px solid #e5e7eb;
            transition: background-color 0.15s ease;
        }}

        tbody tr.benchmark {{
            background-color: #fff4e5;
        }}

        tbody tr:not(.benchmark):nth-child(even) {{
            background-color: #fafaf9;
        }}

        tbody tr:not(.benchmark):hover {{
            background-color: #f5f5f4;
        }}

        tbody td {{
            padding: 0.2rem 1rem;
            border-right: 1px solid #e5e7eb;
            text-align: right;
            white-space: nowrap;
            color: #111;
        }}

        tbody td:first-child {{
            text-align: left;
            font-weight: 500;
            border-right: 1px solid #e5e7eb;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        tbody td:last-child {{
            border-right: none;
        }}

        tbody td.highlight-max {{
            background-color: #d1d5db;
            font-weight: 600;
        }}

        tbody td.highlight-min {{
            background-color: #fef9c3;
            font-weight: 600;
        }}

        tbody td.negative {{
            color: #dc2626;
            font-weight: 600;
        }}

        .table-legend {{
            margin-top: 0;
            padding: 0.5rem 0.75rem;
            background-color: #fafaf9;
            border: 1px solid #e5e7eb;
            border-top: none;
            font-size: 0.75em;
            color: #666;
        }}

        .legend-items {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }}

        .legend-color {{
            display: inline-block;
            width: 0.75rem;
            height: 0.75rem;
            flex-shrink: 0;
            border: 1px solid #ddd;
        }}

        .legend-color.max {{
            background-color: #d1d5db;
        }}

        .legend-color.min {{
            background-color: #fef9c3;
        }}

        .legend-color.benchmark {{
            background-color: #fff4e5;
            border-color: #f90;
        }}

        /* GICS table wider container */
        .table-container.gics-wide {{
            max-width: 60em;
        }}
    </style>
</head>
<body>
<header>
<nav><a href="index.html">Home</a> <a href="newsletter.html">Newsletter</a> <a href="essays.html">Essays</a> <a href="contact.html">Contact</a></nav>
</header>

<main>
<article>
<h1>Monthly Market Update – {month_display}</h1>

<p>This update includes performance data and commentary across asset classes and strategies.</p>

<p>All tables are sorted by 1-month performance by default, with benchmark rows highlighted where relevant.</p>

<p>Data is current as of end-{month_display}.</p>

{''.join(table_sections)}

{thought_html}

{thanks_html}

</article>
</main>

<script>
// ============================================
// TABLE CONFIGURATION & DATA
// ============================================

const tableConfig = {{
{','.join(js_table_configs)}
}};

// ============================================
// SORT STATE MANAGEMENT
// ============================================

const sortStates = {{}};

Object.keys(tableConfig).forEach(key => {{
    sortStates[key] = {{ column: 0, direction: 'desc' }};
}});

// ============================================
// UTILITY FUNCTIONS
// ============================================

function getMinMax(tableKey, colIndex) {{
    const data = tableConfig[tableKey].data;
    const validValues = data
        .map(row => row.values[colIndex])
        .filter(v => v !== null && v !== undefined);
    
    if (validValues.length === 0) {{
        return {{ max: NaN, min: NaN }};
    }}
    
    return {{
        max: Math.max(...validValues),
        min: Math.min(...validValues),
    }};
}}

function formatValue(val) {{
    if (val === null || val === undefined) return '−';
    return `${{val.toFixed(2)}}%`;
}}

function getCellHighlight(tableKey, value, colIndex) {{
    if (value === null || value === undefined) return '';
    const {{ min, max }} = getMinMax(tableKey, colIndex);
    if (value === max) return 'highlight-max';
    if (value === min) return 'highlight-min';
    return '';
}}

// ============================================
// SORTING & RENDERING
// ============================================

function handleSort(tableKey, colIndex) {{
    if (!sortStates[tableKey]) {{
        console.error(`Table key "${{tableKey}}" not found in sortStates`);
        return;
    }}
    
    const state = sortStates[tableKey];
    
    if (state.column === colIndex) {{
        state.direction = state.direction === 'desc' ? 'asc' : 'desc';
    }} else {{
        state.column = colIndex;
        state.direction = 'desc';
    }}
    
    renderTable(tableKey);
    updateSortIndicators(tableKey);
}}

function renderTable(tableKey) {{
    const config = tableConfig[tableKey];
    const state = sortStates[tableKey];
    
    if (!config) {{
        console.error(`Table configuration for "${{tableKey}}" not found`);
        return;
    }}
    
    let sortedData = [...config.data];
    
    if (state.column !== null) {{
        sortedData.sort((a, b) => {{
            const aVal = a.values[state.column];
            const bVal = b.values[state.column];
            
            if (aVal === null || aVal === undefined) return 1;
            if (bVal === null || bVal === undefined) return -1;
            
            return state.direction === 'desc' ? bVal - aVal : aVal - bVal;
        }});
    }}
    
    const tbody = document.getElementById(config.bodyId);
    if (!tbody) {{
        console.error(`Table body with ID "${{config.bodyId}}" not found`);
        return;
    }}
    
    tbody.innerHTML = '';
    
    sortedData.forEach(row => {{
        const tr = document.createElement('tr');
        if (row.isBenchmark) tr.classList.add('benchmark');
        
        const nameCell = document.createElement('td');
        nameCell.textContent = row.name;
        tr.appendChild(nameCell);
        
        row.values.forEach((val, colIdx) => {{
            const td = document.createElement('td');
            td.textContent = formatValue(val);
            
            const highlightClass = getCellHighlight(tableKey, val, colIdx);
            if (highlightClass) td.classList.add(highlightClass);
            if (val !== null && val < 0) td.classList.add('negative');
            
            tr.appendChild(td);
        }});
        
        tbody.appendChild(tr);
    }});
}}

function updateSortIndicators(tableKey) {{
    const config = tableConfig[tableKey];
    const state = sortStates[tableKey];
    const table = document.getElementById(config.tableId);
    
    if (!table) {{
        console.error(`Table with ID "${{config.tableId}}" not found`);
        return;
    }}
    
    const headers = table.querySelectorAll('.column-header th');
    
    headers.forEach((th, idx) => {{
        const div = th.querySelector('.sort-header');
        if (!div) return;
        
        const existingChevron = div.querySelector('.chevron');
        if (existingChevron) existingChevron.remove();
        
        if (idx - 1 === state.column) {{
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'chevron');
            svg.setAttribute('viewBox', '0 0 24 24');
            svg.setAttribute('fill', 'none');
            svg.setAttribute('stroke', 'currentColor');
            svg.setAttribute('stroke-width', '2');
            svg.setAttribute('stroke-linecap', 'round');
            svg.setAttribute('stroke-linejoin', 'round');
            
            const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            if (state.direction === 'desc') {{
                polyline.setAttribute('points', '6 9 12 15 18 9');
            }} else {{
                polyline.setAttribute('points', '18 15 12 9 6 15');
            }}
            svg.appendChild(polyline);
            div.appendChild(svg);
        }}
    }});
}}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {{
    Object.keys(tableConfig).forEach(tableKey => {{
        renderTable(tableKey);
        updateSortIndicators(tableKey);
    }});
}});
</script>

</body>
</html>'''
    
    return full_html

# =============================================================================
# MAIN
# =============================================================================

def get_previous_month():
    """Get YYYY-MM for the previous month"""
    today = datetime.now()
    first_of_month = today.replace(day=1)
    last_month = first_of_month - timedelta(days=1)
    return last_month.strftime('%Y-%m')

def main():
    parser = argparse.ArgumentParser(description='Generate newsletter HTML')
    parser.add_argument('--month', default=None,
                        help='Month in YYYY-MM format (default: previous month)')
    parser.add_argument('--config', default='fund_config.xlsx',
                        help='Path to fund config Excel')
    parser.add_argument('--data', default=None,
                        help='Path to performance CSV (default: most recent)')
    parser.add_argument('--benchmarks', default='benchmark_data.csv',
                        help='Path to auto-fetched benchmark CSV')
    parser.add_argument('--manual', default='manual_data.xlsx',
                        help='Path to manual data Excel')
    parser.add_argument('--commentary', default='commentary.md',
                        help='Path to commentary markdown')
    parser.add_argument('--output', default=None,
                        help='Output HTML path (default: newsletter_YYYY_MM.html)')
    parser.add_argument('--preview', action='store_true',
                        help='Open in browser after generation')
    
    args = parser.parse_args()
    
    # Default to previous month if not specified
    if args.month is None:
        args.month = get_previous_month()
    
    print(f"Generating newsletter for {args.month}...")
    
    # Load fund config
    print("\nLoading fund config...")
    config_df = load_fund_config(args.config)
    
    # Load all data sources
    print("\nLoading data sources...")
    perf_df = load_performance_data(args.data)
    benchmark_df = load_benchmark_data(args.benchmarks)
    manual_df = load_manual_data(args.manual)
    
    # Combine all performance data
    print("\nCombining data sources...")
    
    # Standardize column names across all sources
    def standardize_columns(df):
        df = df.copy()
        # Map various column name formats to standard names
        renames = {
            '1M': '1 Mth', '1 Mth': '1 Mth', '1_mo': '1 Mth',
            '3M': '3 Mth', '3 Mth': '3 Mth', '3_mos': '3 Mth',
            '1Y p.a.': '1 Yr pa', '1 Yr pa': '1 Yr pa', '1_yr': '1 Yr pa',
            '3Y p.a.': '3 Yr pa', '3 Yr pa': '3 Yr pa', '3_yrs': '3 Yr pa',
            '5Y p.a.': '5 Yr pa', '5 Yr pa': '5 Yr pa', '5_yrs': '5 Yr pa',
            '10Y p.a.': '10 Yr pa', '10 Yr pa': '10 Yr pa', '10_yrs': '10 Yr pa',
        }
        for old, new in renames.items():
            if old in df.columns and old != new:
                df = df.rename(columns={old: new})
        return df
    
    all_perf = [standardize_columns(perf_df)]
    if len(benchmark_df) > 0:
        all_perf.append(standardize_columns(benchmark_df))
    if len(manual_df) > 0:
        all_perf.append(standardize_columns(manual_df))
    
    combined_perf = pd.concat(all_perf, ignore_index=True)
    
    # Remove duplicates (prefer benchmark/manual over scraped for same fund name)
    # Keep last occurrence (benchmark/manual data added last takes precedence)
    combined_perf = combined_perf.drop_duplicates(subset=['Fund Name'], keep='last')
    print(f"Combined performance data: {len(combined_perf)} unique funds")
    
    # Filter out stale data (only include funds with current month's data)
    stale_funds = []
    if 'As at Date' in combined_perf.columns:
        # Parse target month from args.month (format: YYYY-MM)
        target_year, target_month = map(int, args.month.split('-'))
        
        # Month name mapping
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        target_month_name = month_names[target_month]
        
        def is_current_month(date_str):
            """Check if date string matches target month"""
            if pd.isna(date_str) or date_str == 'Date not found':
                return True  # Keep funds without date info (manual entries, benchmarks)
            
            date_str = str(date_str)
            # Expected format: "As at 30 Nov 2025" or "30 Nov 2025"
            # Check if target month and year are in the string
            if target_month_name in date_str and str(target_year) in date_str:
                return True
            return False
        
        # Identify stale funds before filtering
        for _, row in combined_perf.iterrows():
            date_val = row.get('As at Date', '')
            if not is_current_month(date_val):
                stale_funds.append({
                    'Fund Name': row['Fund Name'],
                    'As at Date': date_val
                })
        
        # Filter to current month only
        combined_perf = combined_perf[combined_perf['As at Date'].apply(is_current_month)]
        
        if stale_funds:
            print(f"\n⚠️  Filtered out {len(stale_funds)} funds with stale data (not {target_month_name} {target_year})")
    
    print("\nLoading commentary...")
    commentary = load_commentary(args.commentary)
    
    # Merge data
    print("\nMerging with config...")
    merged = merge_data(config_df, combined_perf)
    
    # Check coverage
    total = len(config_df)
    with_data = merged['1 Mth'].notna().sum()
    print(f"Data coverage: {with_data}/{total} funds ({with_data/total*100:.1f}%)")
    
    # Show missing funds
    missing = merged[merged['1 Mth'].isna()]['Fund Name'].tolist()
    if missing:
        print(f"\nMissing data for {len(missing)} funds:")
        for f in missing[:10]:
            print(f"  - {f}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")
    
    # Generate stale/missing funds report
    report_path = f"fund_report_{args.month.replace('-', '_')}.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"Fund Data Report for {args.month}\n")
        f.write("=" * 50 + "\n\n")
        
        if stale_funds:
            f.write(f"STALE DATA ({len(stale_funds)} funds) - excluded from newsletter:\n")
            f.write("-" * 50 + "\n")
            for fund in stale_funds:
                f.write(f"  {fund['Fund Name']}\n")
                f.write(f"    Date: {fund['As at Date']}\n")
            f.write("\n")
        
        if missing:
            f.write(f"MISSING DATA ({len(missing)} funds) - no performance data found:\n")
            f.write("-" * 50 + "\n")
            for fund_name in missing:
                f.write(f"  {fund_name}\n")
            f.write("\n")
        
        if not stale_funds and not missing:
            f.write("✅ All funds have current data!\n")
        
        f.write(f"\nSummary:\n")
        f.write(f"  Total funds in config: {total}\n")
        f.write(f"  With current data: {with_data}\n")
        f.write(f"  Stale data: {len(stale_funds)}\n")
        f.write(f"  Missing data: {len(missing)}\n")
    
    print(f"\n📄 Fund report saved to: {report_path}")
    
    # Generate HTML
    print("\nGenerating HTML...")
    html = generate_full_html(merged, commentary, args.month, args.manual)

    # Save
    output_path = args.output or f"newsletter_{args.month.replace('-', '_')}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Newsletter saved to: {output_path}")
    
    # Preview
    if args.preview:
        print("Opening in browser...")
        webbrowser.open(f'file://{os.path.abspath(output_path)}')

if __name__ == '__main__':
    main()
