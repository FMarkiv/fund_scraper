"""
Unit tests for fetch_benchmarks.py
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetch_benchmarks import (
    get_month_end_date,
    get_price_at_date,
    calculate_returns,
    get_last_month_end,
    BENCHMARKS
)


class TestGetMonthEndDate:
    """Tests for get_month_end_date function"""

    def test_january(self):
        """Should return Jan 31"""
        result = get_month_end_date(2025, 1)
        assert result.day == 31
        assert result.month == 1

    def test_february_non_leap(self):
        """Should return Feb 28 for non-leap year"""
        result = get_month_end_date(2025, 2)
        assert result.day == 28
        assert result.month == 2

    def test_february_leap(self):
        """Should return Feb 29 for leap year"""
        result = get_month_end_date(2024, 2)
        assert result.day == 29
        assert result.month == 2

    def test_april(self):
        """Should return Apr 30"""
        result = get_month_end_date(2025, 4)
        assert result.day == 30
        assert result.month == 4

    def test_december(self):
        """Should return Dec 31"""
        result = get_month_end_date(2025, 12)
        assert result.day == 31
        assert result.month == 12


class TestGetPriceAtDate:
    """Tests for get_price_at_date function"""

    def test_exact_date_match(self):
        """Should return price on exact date"""
        dates = pd.date_range('2025-01-01', periods=5, freq='D')
        prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0], index=dates)

        result = get_price_at_date(prices, datetime(2025, 1, 3))

        assert result == 102.0

    def test_weekend_fallback(self):
        """Should fall back to previous day for weekend"""
        # Create prices for Mon-Fri only
        dates = [datetime(2025, 1, 6), datetime(2025, 1, 7), datetime(2025, 1, 8),
                 datetime(2025, 1, 9), datetime(2025, 1, 10)]
        prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0], index=dates)

        # Saturday Jan 11 should fall back to Friday Jan 10
        result = get_price_at_date(prices, datetime(2025, 1, 11))

        assert result == 104.0

    def test_none_prices(self):
        """Should return None for None prices"""
        result = get_price_at_date(None, datetime(2025, 1, 1))
        assert result is None

    def test_empty_prices(self):
        """Should return None for empty prices"""
        prices = pd.Series([], dtype=float)
        result = get_price_at_date(prices, datetime(2025, 1, 1))
        assert result is None

    def test_string_date(self):
        """Should handle string date input"""
        dates = pd.date_range('2025-01-01', periods=5, freq='D')
        prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0], index=dates)

        result = get_price_at_date(prices, '2025-01-03')

        assert result == 102.0

    def test_date_not_found(self):
        """Should return None if date not found within lookback"""
        dates = pd.date_range('2025-01-01', periods=3, freq='D')
        prices = pd.Series([100.0, 101.0, 102.0], index=dates)

        # Date far in future, beyond lookback
        result = get_price_at_date(prices, datetime(2025, 1, 15), lookback_days=5)

        assert result is None


class TestCalculateReturns:
    """Tests for calculate_returns function"""

    def test_basic_returns(self):
        """Should calculate returns correctly"""
        current_date = datetime(2025, 1, 31)
        current_price = 110.0

        # Create price history
        dates = pd.date_range('2024-01-01', '2025-01-31', freq='D')
        prices = pd.Series([100.0] * len(dates), index=dates)
        prices.iloc[-1] = 110.0  # Current price
        prices.iloc[-31] = 105.0  # 1 month ago (approx)

        result = calculate_returns(current_price, prices, current_date)

        assert '1 Mth' in result
        assert '3 Mth' in result
        assert '1 Yr pa' in result
        assert '3 Yr pa' in result

    def test_none_current_price(self):
        """Should return None values for None current price"""
        dates = pd.date_range('2024-01-01', '2025-01-31', freq='D')
        prices = pd.Series([100.0] * len(dates), index=dates)

        result = calculate_returns(None, prices, datetime(2025, 1, 31))

        assert result['1 Mth'] is None
        assert result['1 Yr pa'] is None

    def test_currency_adjustment(self):
        """Should apply currency adjustment when specified"""
        current_date = datetime(2025, 1, 31)
        current_price = 2000.0  # USD gold price

        dates = pd.date_range('2024-01-01', '2025-01-31', freq='D')
        prices = pd.Series([1900.0] * len(dates), index=dates)
        prices.iloc[-1] = 2000.0

        # AUD/USD rates
        audusd = pd.Series([0.65] * len(dates), index=dates)

        result = calculate_returns(
            current_price, prices, current_date,
            audusd_prices=audusd, currency_adjust=True
        )

        assert result['1 Mth'] is not None


class TestGetLastMonthEnd:
    """Tests for get_last_month_end function"""

    @patch('fetch_benchmarks.datetime')
    def test_middle_of_month(self, mock_datetime):
        """Should return last day of previous month"""
        mock_datetime.now.return_value = datetime(2025, 3, 15)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        result = get_last_month_end()

        assert result.month == 2
        assert result.day == 28
        assert result.year == 2025

    @patch('fetch_benchmarks.datetime')
    def test_first_of_month(self, mock_datetime):
        """Should return last day of previous month from first day"""
        mock_datetime.now.return_value = datetime(2025, 4, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        result = get_last_month_end()

        assert result.month == 3
        assert result.day == 31

    @patch('fetch_benchmarks.datetime')
    def test_january(self, mock_datetime):
        """Should return December 31 of previous year"""
        mock_datetime.now.return_value = datetime(2025, 1, 15)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        result = get_last_month_end()

        assert result.month == 12
        assert result.day == 31
        assert result.year == 2024


class TestBenchmarksConfig:
    """Tests for BENCHMARKS configuration"""

    def test_required_benchmarks_exist(self):
        """Should have expected benchmark entries"""
        expected = [
            'Spot Gold - AU$ / Oz',
            'Spot Silver - AU$ / Oz',
            'Bitcoin(BTC) Price in AUD',
            'Ethereum(ETH) Price in AUD'
        ]
        for name in expected:
            assert name in BENCHMARKS

    def test_benchmark_structure(self):
        """Each benchmark should have required fields"""
        for name, config in BENCHMARKS.items():
            assert 'ticker' in config, f"{name} missing ticker"
            assert 'currency_adjust' in config, f"{name} missing currency_adjust"

    def test_gold_config(self):
        """Gold should be configured for currency adjustment"""
        gold = BENCHMARKS['Spot Gold - AU$ / Oz']
        assert gold['ticker'] == 'GC=F'
        assert gold['currency_adjust'] is True

    def test_btc_config(self):
        """BTC-AUD should not need currency adjustment"""
        btc = BENCHMARKS['Bitcoin(BTC) Price in AUD']
        assert btc['ticker'] == 'BTC-AUD'
        assert btc['currency_adjust'] is False
