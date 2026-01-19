"""
Benchmark Data Fetcher for ausyield.com.au
Fetches Gold, Silver, BTC, ETH prices and calculates returns

Usage:
    python fetch_benchmarks.py [--date YYYY-MM-DD]

Outputs:
    - benchmark_data.csv: Ready to merge with fund performance data
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import argparse
import time

# =============================================================================
# CONFIGURATION
# =============================================================================

BENCHMARKS = {
    'Spot Gold - AU$ / Oz': {
        'ticker': 'GC=F',  # Gold futures USD
        'currency_adjust': True,  # Multiply by AUD/USD
    },
    'Spot Silver - AU$ / Oz': {
        'ticker': 'SI=F',  # Silver futures USD
        'currency_adjust': True,
    },
    'Bitcoin(BTC) Price in AUD': {
        'ticker': 'BTC-AUD',
        'currency_adjust': False,
    },
    'Ethereum(ETH) Price in AUD': {
        'ticker': 'ETH-AUD',
        'currency_adjust': False,
    },
    'GDX - VanEck Gold Miners ETF': {
        'ticker': 'GDX',
        'currency_adjust': True,  # USD ETF, convert to AUD
    },
}

# AUD/USD for currency conversion
AUDUSD_TICKER = 'AUDUSD=X'

# =============================================================================
# DATA FETCHING
# =============================================================================

def get_month_end_date(year, month):
    """Get the last trading day of a month"""
    # Start with last day of month
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)
    return last_day

def fetch_price_history(ticker, start_date, end_date, retries=3):
    """Fetch price history for a ticker with retry logic"""
    for attempt in range(retries):
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if data.empty:
                print(f"  Warning: No data for {ticker}")
                return None
            if 'Close' not in data.columns:
                # Handle multi-index columns (newer yfinance versions)
                if hasattr(data.columns, 'get_level_values'):
                    # Try to extract Close from multi-index
                    try:
                        return data['Close'][ticker] if ticker in data['Close'].columns else data['Close'].iloc[:, 0]
                    except (KeyError, IndexError):
                        pass
                print(f"  Warning: No 'Close' column for {ticker}")
                return None
            return data['Close']
        except Exception as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                print(f"  Retry {attempt + 1}/{retries} for {ticker} in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  Error fetching {ticker} after {retries} attempts: {e}")
                return None
    return None

def get_price_at_date(prices, target_date, lookback_days=5):
    """Get price at or near a target date (handles weekends/holidays)"""
    if prices is None or len(prices) == 0:
        return None
    
    # Convert target_date to datetime if needed
    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date)
    
    # Convert series to simple date->value dict for easier lookup
    price_dict = {}
    for i in range(len(prices)):
        idx = prices.index[i]
        val = prices.iloc[i]
        # Extract date portion
        if hasattr(idx, 'date'):
            date_key = idx.date()
        else:
            date_key = idx
        price_dict[date_key] = float(val)
    
    # Get target as date
    if hasattr(target_date, 'date'):
        target = target_date.date()
    else:
        target = target_date
    
    # Look for price on or before target date
    for i in range(lookback_days + 1):
        check_date = target - timedelta(days=i)
        if check_date in price_dict:
            return price_dict[check_date]
    
    return None

def calculate_returns(current_price, prices, current_date, audusd_prices=None, currency_adjust=False):
    """Calculate 1M, 3M, 1Y, 3Y returns"""
    
    # Define lookback periods
    periods = {
        '1 Mth': relativedelta(months=1),
        '3 Mth': relativedelta(months=3),
        '1 Yr pa': relativedelta(years=1),
        '3 Yr pa': relativedelta(years=3),
    }
    
    results = {}
    
    for period_name, delta in periods.items():
        past_date = current_date - delta
        past_price = get_price_at_date(prices, past_date)
        
        if past_price is None or current_price is None:
            results[period_name] = None
            continue
        
        # Currency adjustment if needed
        if currency_adjust and audusd_prices is not None:
            current_fx = get_price_at_date(audusd_prices, current_date)
            past_fx = get_price_at_date(audusd_prices, past_date)
            
            if current_fx and past_fx:
                # Convert USD to AUD (divide by AUD/USD rate)
                current_aud = current_price / current_fx
                past_aud = past_price / past_fx
            else:
                current_aud = current_price
                past_aud = past_price
        else:
            current_aud = current_price
            past_aud = past_price
        
        # Calculate return
        total_return = (current_aud - past_aud) / past_aud
        
        # Annualize for 1Y and 3Y
        if 'Yr' in period_name:
            years = int(period_name[0])
            # Already represents total return over the period
            # For "pa" we want annualized
            annualized = ((1 + total_return) ** (1/years)) - 1
            results[period_name] = annualized * 100
        else:
            results[period_name] = total_return * 100
    
    return results

# =============================================================================
# MAIN
# =============================================================================

def get_last_month_end():
    """Get the last day of the previous month"""
    today = datetime.now()
    # First day of current month
    first_of_month = today.replace(day=1)
    # Last day of previous month
    last_month_end = first_of_month - timedelta(days=1)
    return last_month_end

def fetch_all_benchmarks(as_of_date=None):
    """Fetch all benchmark data and calculate returns"""
    
    if as_of_date is None:
        as_of_date = get_last_month_end()
        print(f"Defaulting to end of previous month: {as_of_date.strftime('%Y-%m-%d')}")
    elif isinstance(as_of_date, str):
        as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d')
    
    print(f"Fetching benchmark data as of {as_of_date.strftime('%Y-%m-%d')}...")
    
    # Need 4 years of history for 3Y returns
    start_date = as_of_date - relativedelta(years=4)
    end_date = as_of_date + timedelta(days=1)
    
    # Fetch AUD/USD for currency conversion
    print("Fetching AUD/USD exchange rate...")
    audusd_prices = fetch_price_history(AUDUSD_TICKER, start_date, end_date)
    
    results = []
    
    for name, config in BENCHMARKS.items():
        ticker = config['ticker']
        currency_adjust = config.get('currency_adjust', False)
        
        print(f"Fetching {name} ({ticker})...")
        
        # Fetch price history
        prices = fetch_price_history(ticker, start_date, end_date)
        
        if prices is None:
            print(f"  Skipping {name} - no data")
            continue
        
        # Get current price
        current_price = get_price_at_date(prices, as_of_date)
        
        if current_price is None:
            print(f"  Skipping {name} - no current price")
            continue
        
        # Calculate returns
        returns = calculate_returns(
            current_price, 
            prices, 
            as_of_date,
            audusd_prices if currency_adjust else None,
            currency_adjust
        )
        
        # Build row
        row = {
            'Fund Name': name,
            '1 Mth': returns.get('1 Mth'),
            '3 Mth': returns.get('3 Mth'),
            '1 Yr pa': returns.get('1 Yr pa'),
            '3 Yr pa': returns.get('3 Yr pa'),
            'Data Source': 'yfinance',
            'As at Date': as_of_date.strftime('%Y-%m-%d'),
        }
        
        results.append(row)
        
        # Print summary
        m1 = f"{returns['1 Mth']:.2f}%" if returns['1 Mth'] else 'N/A'
        y1 = f"{returns['1 Yr pa']:.2f}%" if returns['1 Yr pa'] else 'N/A'
        y3 = f"{returns['3 Yr pa']:.2f}%" if returns['3 Yr pa'] else 'N/A'
        print(f"  ✓ 1M: {m1}, 1Y: {y1}, 3Y: {y3}")
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description='Fetch benchmark data')
    parser.add_argument('--date', default=None,
                        help='As-of date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--output', default='benchmark_data.csv',
                        help='Output CSV path')
    
    args = parser.parse_args()
    
    # Fetch data
    df = fetch_all_benchmarks(args.date)
    
    if len(df) == 0:
        print("\n❌ No benchmark data fetched")
        return
    
    # Save to CSV
    df.to_csv(args.output, index=False)
    
    print(f"\n✅ Saved {len(df)} benchmarks to {args.output}")
    print("\nData preview:")
    print(df.to_string(index=False))

if __name__ == '__main__':
    main()
