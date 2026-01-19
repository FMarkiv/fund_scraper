"""
Merge S&P PDF scraper output into manual_data.xlsx
Usage: python merge_sp_data.py
"""

import pandas as pd
from datetime import datetime

# Filename to Fund Name mapping
# IMPORTANT: More specific patterns first, generic last
FILENAME_MAP = [
    ('all-ordinaries-gold', 'S&P/ASX All Ordinaries Gold Accumulation'),
    ('financial-x-a-reit', 'S&P/ASX 200 Fin-x-Prop Accumulation'),  # Must be before a-reit
    ('a-reit-sector', 'S&P/ASX 200 A-REIT Accumulation'),
    ('communication-services', 'S&P/ASX 200 Telecoms Accumulation'),
    ('consumer-discretionary', 'S&P/ASX 200 Discretion Accumulation'),
    ('consumer-staples', 'S&P/ASX 200 Staples Accumulation'),
    ('energy-sector', 'S&P/ASX 200 Energy Accumulation'),
    ('health-care', 'S&P/ASX 200 HealthCare Accumulation'),
    ('information-technology', 'S&P/ASX 200 Info Tech Accumulation'),
    ('materials-sector', 'S&P/ASX 200 Materials Accumulation'),
    ('utilities-sector', 'S&P/ASX 200 Utilities Accumulation'),
    ('industrial', 'S&P/ASX 200 Industrial Accumulation'),
    ('emerging-companies', 'S&P/ASX Emerging Companies Accumulation'),
    ('midcap-50', 'S&P/ASX Midcap 50 Accumulation'),
    ('small-ordinaries', 'S&P/ASX Small Ords Accumulation'),
    ('asx-200 ', 'S&P/ASX 200 Accumulation'),  # Space after to avoid matching sector files
    ('asx-200.', 'S&P/ASX 200 Accumulation'),  # Period for end of filename
    ('fs-sp-asx-200 ', 'S&P/ASX 200 Accumulation'),
]

def parse_pct(val):
    """Convert percentage string to float"""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return val
    return float(str(val).replace('%', '').strip())

def match_filename(filename):
    """Match filename to fund name - checks most specific patterns first"""
    filename_lower = filename.lower()
    for pattern, fund_name in FILENAME_MAP:
        if pattern in filename_lower:
            return fund_name
    return None

def main():
    # Load S&P PDF scraper output
    try:
        sp_df = pd.read_csv('performance_data.csv')
    except FileNotFoundError:
        print("❌ performance_data.csv not found. Run pdfscraper.py first.")
        return
    
    print(f"Loaded {len(sp_df)} rows from performance_data.csv")
    
    # Map filenames to fund names
    sp_df['Fund Name'] = sp_df['filename'].apply(match_filename)
    
    # Drop duplicates (keep first)
    sp_df = sp_df.drop_duplicates(subset=['Fund Name'], keep='first')
    
    # Remove unmapped rows
    unmapped = sp_df[sp_df['Fund Name'].isna()]
    if len(unmapped) > 0:
        print(f"\n⚠️  Could not map {len(unmapped)} files:")
        for f in unmapped['filename'].tolist():
            print(f"   - {f}")
    
    sp_df = sp_df[sp_df['Fund Name'].notna()]
    print(f"Mapped {len(sp_df)} funds")
    
    # Rename columns to match manual_data format
    sp_df = sp_df.rename(columns={
        '1_mo': '1 Mth',
        '3_mos': '3 Mth',
        '1_yr': '1 Yr pa',
        '3_yrs': '3 Yr pa',
        '5_yrs': '5 Yr pa',
        '10_yrs': '10 Yr pa',
    })
    
    # Parse percentages
    for col in ['1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa', '5 Yr pa', '10 Yr pa']:
        if col in sp_df.columns:
            sp_df[col] = sp_df[col].apply(parse_pct)
    
    # Add last updated date
    sp_df['Last Updated'] = datetime.now().strftime('%Y-%m-%d')
    
    # Select final columns
    final_cols = ['Fund Name', '1 Mth', '3 Mth', '1 Yr pa', '3 Yr pa', '5 Yr pa', '10 Yr pa', 'Last Updated']
    sp_df = sp_df[final_cols]
    
    # Load existing manual_data.xlsx and update GICS sheet
    try:
        with pd.ExcelFile('manual_data.xlsx') as xls:
            cpi_df = pd.read_excel(xls, sheet_name='CPI_Benchmarks')
            other_df = pd.read_excel(xls, sheet_name='Other_Manual')
            instructions_df = pd.read_excel(xls, sheet_name='Instructions')
    except FileNotFoundError:
        print("❌ manual_data.xlsx not found")
        return
    
    # Write back with updated GICS sheet
    with pd.ExcelWriter('manual_data.xlsx', engine='openpyxl') as writer:
        cpi_df.to_excel(writer, sheet_name='CPI_Benchmarks', index=False)
        sp_df.to_excel(writer, sheet_name='GICS_Sectors', index=False)
        other_df.to_excel(writer, sheet_name='Other_Manual', index=False)
        instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
    
    print(f"\n✅ Updated manual_data.xlsx with {len(sp_df)} GICS sectors")
    print("\nData written:")
    print(sp_df.to_string(index=False))

if __name__ == '__main__':
    main()
