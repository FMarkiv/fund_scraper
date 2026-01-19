"""
Fund Coverage Checker
- Shows which funds failed to scrape
- Compares two months to track additions/subtractions

Usage:
    python check_coverage.py                     # Show failed scrapes
    python check_coverage.py --compare old.csv   # Compare to previous month
"""

import pandas as pd
import argparse
import glob
import os

def get_latest_csv():
    """Find most recent fund_performance CSV"""
    csvs = glob.glob('fund_performance_*.csv')
    if not csvs:
        return None
    return max(csvs, key=os.path.getmtime)

def check_failed_scrapes(links_file='fund_links.xlsx', perf_file=None):
    """Show funds that failed to scrape"""
    
    if perf_file is None:
        perf_file = get_latest_csv()
        if perf_file is None:
            print("❌ No fund_performance_*.csv found")
            return
    
    print(f"Comparing:")
    print(f"  Links: {links_file}")
    print(f"  Scraped: {perf_file}")
    print()
    
    # Load files
    links_df = pd.read_excel(links_file)
    perf_df = pd.read_csv(perf_file)
    
    # Strip whitespace
    links_df['Fund Name'] = links_df['Fund Name'].str.strip()
    perf_df['Fund Name'] = perf_df['Fund Name'].str.strip()
    
    # Find differences
    expected = set(links_df['Fund Name'].tolist())
    scraped = set(perf_df['Fund Name'].tolist())
    
    failed = expected - scraped
    extra = scraped - expected  # Shouldn't happen, but check
    
    print("=" * 70)
    print(f"SCRAPE RESULTS")
    print("=" * 70)
    print(f"Expected (in fund_links.xlsx): {len(expected)}")
    print(f"Scraped successfully:          {len(scraped)}")
    print(f"Failed:                        {len(failed)}")
    print()
    
    if failed:
        print("❌ FAILED TO SCRAPE:")
        print("-" * 70)
        for fund in sorted(failed):
            # Get URL from links file
            url_row = links_df[links_df['Fund Name'] == fund]
            url = url_row['URL'].iloc[0] if len(url_row) > 0 else 'URL not found'
            print(f"  {fund}")
            print(f"    → {url}")
        print()
    
    if extra:
        print("⚠️  SCRAPED BUT NOT IN LINKS (unexpected):")
        for fund in sorted(extra):
            print(f"  {fund}")
        print()
    
    return failed

def compare_months(current_file=None, previous_file=None):
    """Compare two performance files to track changes"""
    
    if current_file is None:
        current_file = get_latest_csv()
    
    if current_file is None or previous_file is None:
        print("❌ Need both current and previous CSV files")
        print("Usage: python check_coverage.py --compare previous_month.csv")
        return
    
    print(f"Comparing:")
    print(f"  Current:  {current_file}")
    print(f"  Previous: {previous_file}")
    print()
    
    # Load files
    current_df = pd.read_csv(current_file)
    previous_df = pd.read_csv(previous_file)
    
    # Strip whitespace
    current_df['Fund Name'] = current_df['Fund Name'].str.strip()
    previous_df['Fund Name'] = previous_df['Fund Name'].str.strip()
    
    current = set(current_df['Fund Name'].tolist())
    previous = set(previous_df['Fund Name'].tolist())
    
    added = current - previous
    removed = previous - current
    unchanged = current & previous
    
    print("=" * 70)
    print("MONTH-OVER-MONTH COMPARISON")
    print("=" * 70)
    print(f"Previous month: {len(previous)} funds")
    print(f"Current month:  {len(current)} funds")
    print(f"Net change:     {len(current) - len(previous):+d}")
    print()
    
    if added:
        print(f"➕ ADDED ({len(added)} funds):")
        print("-" * 70)
        for fund in sorted(added):
            print(f"  {fund}")
        print()
    
    if removed:
        print(f"➖ REMOVED ({len(removed)} funds):")
        print("-" * 70)
        for fund in sorted(removed):
            print(f"  {fund}")
        print()
    
    if not added and not removed:
        print("✓ No changes - same funds in both months")
    
    return added, removed

def main():
    parser = argparse.ArgumentParser(description='Check fund coverage')
    parser.add_argument('--links', default='fund_links.xlsx',
                        help='Fund links Excel file')
    parser.add_argument('--current', default=None,
                        help='Current performance CSV (default: most recent)')
    parser.add_argument('--compare', default=None,
                        help='Previous month CSV to compare against')
    
    args = parser.parse_args()
    
    if args.compare:
        compare_months(args.current, args.compare)
    else:
        check_failed_scrapes(args.links, args.current)

if __name__ == '__main__':
    main()
