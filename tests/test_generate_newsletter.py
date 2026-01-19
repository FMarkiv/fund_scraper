"""
Unit tests for generate_newsletter.py
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, mock_open
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_newsletter import (
    parse_percentage,
    get_previous_month,
    merge_data,
    calculate_outperformance,
    load_commentary,
    commentary_to_html,
    COLUMN_MAP
)


class TestParsePercentage:
    """Tests for parse_percentage function"""

    def test_parse_float(self):
        """Should return float as-is"""
        assert parse_percentage(5.5) == 5.5
        assert parse_percentage(-3.2) == -3.2
        assert parse_percentage(0.0) == 0.0

    def test_parse_integer(self):
        """Should convert integer to float"""
        assert parse_percentage(5) == 5.0
        assert parse_percentage(-3) == -3.0

    def test_parse_percentage_string(self):
        """Should parse percentage strings"""
        assert parse_percentage("5.5%") == 5.5
        assert parse_percentage("-3.2%") == -3.2
        assert parse_percentage("10%") == 10.0

    def test_parse_string_without_percent(self):
        """Should parse numeric strings without percent sign"""
        assert parse_percentage("5.5") == 5.5
        assert parse_percentage("-3.2") == -3.2

    def test_parse_string_with_comma(self):
        """Should handle strings with commas"""
        assert parse_percentage("1,234.5%") == 1234.5
        assert parse_percentage("1,000") == 1000.0

    def test_parse_none(self):
        """Should return None for None input"""
        assert parse_percentage(None) is None

    def test_parse_nan(self):
        """Should return None for NaN values"""
        assert parse_percentage(float('nan')) is None
        assert parse_percentage(pd.NA) is None

    def test_parse_dash(self):
        """Should return None for dash placeholders"""
        assert parse_percentage("-") is None
        assert parse_percentage("-%") is None

    def test_parse_empty_string(self):
        """Should return None for empty strings"""
        assert parse_percentage("") is None
        assert parse_percentage("   ") is None

    def test_parse_invalid_string(self):
        """Should return None for invalid strings"""
        assert parse_percentage("nan") is None
        assert parse_percentage("None") is None
        assert parse_percentage("N/A") is None


class TestGetPreviousMonth:
    """Tests for get_previous_month function"""

    @patch('generate_newsletter.datetime')
    def test_middle_of_year(self, mock_datetime):
        """Should return previous month for middle of year"""
        mock_datetime.now.return_value = datetime(2025, 6, 15)
        mock_datetime.strptime = datetime.strptime
        result = get_previous_month()
        assert result == "2025-05"

    @patch('generate_newsletter.datetime')
    def test_january(self, mock_datetime):
        """Should return December of previous year for January"""
        mock_datetime.now.return_value = datetime(2025, 1, 15)
        mock_datetime.strptime = datetime.strptime
        result = get_previous_month()
        assert result == "2024-12"

    @patch('generate_newsletter.datetime')
    def test_first_day_of_month(self, mock_datetime):
        """Should handle first day of month correctly"""
        mock_datetime.now.return_value = datetime(2025, 3, 1)
        mock_datetime.strptime = datetime.strptime
        result = get_previous_month()
        assert result == "2025-02"


class TestMergeData:
    """Tests for merge_data function"""

    def test_basic_merge(self):
        """Should merge config with performance data"""
        config_df = pd.DataFrame({
            'Fund Name': ['Fund A', 'Fund B'],
            'Asset Class': ['Equities', 'Fixed Income']
        })
        perf_df = pd.DataFrame({
            'Fund Name': ['Fund A', 'Fund B'],
            '1M': ['5.5%', '2.1%'],
            '3M': ['10.0%', '5.5%']
        })

        result = merge_data(config_df, perf_df)

        assert len(result) == 2
        assert '1 Mth' in result.columns
        assert '3 Mth' in result.columns
        assert result.loc[result['Fund Name'] == 'Fund A', '1 Mth'].iloc[0] == 5.5

    def test_merge_with_missing_fund(self):
        """Should handle funds in config but not in performance"""
        config_df = pd.DataFrame({
            'Fund Name': ['Fund A', 'Fund B', 'Fund C'],
            'Asset Class': ['Equities', 'Fixed Income', 'Equities']
        })
        perf_df = pd.DataFrame({
            'Fund Name': ['Fund A', 'Fund B'],
            '1M': ['5.5%', '2.1%']
        })

        result = merge_data(config_df, perf_df)

        assert len(result) == 3
        assert pd.isna(result.loc[result['Fund Name'] == 'Fund C', '1 Mth'].iloc[0])

    def test_column_mapping(self):
        """Should map column names correctly"""
        config_df = pd.DataFrame({
            'Fund Name': ['Fund A'],
            'Asset Class': ['Equities']
        })
        perf_df = pd.DataFrame({
            'Fund Name': ['Fund A'],
            '1M': ['5.5%'],
            '3M': ['10.0%'],
            '1Y p.a.': ['15.0%'],
            '3Y p.a.': ['12.0%']
        })

        result = merge_data(config_df, perf_df)

        assert '1 Mth' in result.columns
        assert '3 Mth' in result.columns
        assert '1 Yr pa' in result.columns
        assert '3 Yr pa' in result.columns


class TestCalculateOutperformance:
    """Tests for calculate_outperformance function"""

    def test_basic_outperformance(self):
        """Should calculate percentage of funds outperforming benchmark"""
        data = pd.DataFrame({
            'Fund Name': ['Fund A', 'Fund B', 'Fund C', 'Benchmark'],
            '1 Mth': [5.0, 3.0, 7.0, 4.0],
            '3 Mth': [10.0, 8.0, 12.0, 9.0],
            '1 Yr pa': [15.0, 12.0, 18.0, 14.0],
            '3 Yr pa': [10.0, 8.0, 12.0, 9.0],
            'Is Benchmark': [False, False, False, True]
        })

        result = calculate_outperformance(data)

        # 2 out of 3 funds outperform in 1 Mth (5.0 > 4.0, 7.0 > 4.0)
        assert result['1 Mth'] == '66.7%'

    def test_no_benchmark(self):
        """Should return empty dict if no benchmark exists"""
        data = pd.DataFrame({
            'Fund Name': ['Fund A', 'Fund B'],
            '1 Mth': [5.0, 3.0],
            'Is Benchmark': [False, False]
        })

        result = calculate_outperformance(data)

        assert result == {}

    def test_with_nan_values(self):
        """Should handle NaN values correctly"""
        data = pd.DataFrame({
            'Fund Name': ['Fund A', 'Fund B', 'Fund C', 'Benchmark'],
            '1 Mth': [5.0, None, 7.0, 4.0],
            'Is Benchmark': [False, False, False, True]
        })

        result = calculate_outperformance(data)

        # Only 2 valid funds, both outperform (5.0 > 4.0, 7.0 > 4.0)
        assert result['1 Mth'] == '100.0%'


class TestLoadCommentary:
    """Tests for load_commentary function"""

    def test_parse_sections(self):
        """Should parse markdown sections correctly"""
        mock_content = """## Fixed Income
This is the fixed income commentary.
More text here.

## Equities
Equities commentary here.

## Thought of the Month
Monthly thoughts.
"""
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('os.path.exists', return_value=True):
                result = load_commentary('test.md')

        assert 'Fixed Income' in result
        assert 'Equities' in result
        assert 'Thought of the Month' in result
        assert 'fixed income commentary' in result['Fixed Income']

    def test_missing_file(self):
        """Should return empty dict for missing file"""
        with patch('os.path.exists', return_value=False):
            result = load_commentary('nonexistent.md')

        assert result == {}


class TestCommentaryToHtml:
    """Tests for commentary_to_html function"""

    def test_basic_markdown(self):
        """Should convert markdown to HTML"""
        md = "This is **bold** text."
        result = commentary_to_html(md)

        assert '<strong>bold</strong>' in result

    def test_placeholder_text(self):
        """Should return empty string for placeholder text"""
        result = commentary_to_html("[Your commentary here]")
        assert result == ''

    def test_empty_content(self):
        """Should handle empty content"""
        assert commentary_to_html('') == ''
        assert commentary_to_html(None) == ''


class TestColumnMap:
    """Tests for COLUMN_MAP constant"""

    def test_column_map_keys(self):
        """Should have expected source column names"""
        assert '1M' in COLUMN_MAP
        assert '3M' in COLUMN_MAP
        assert '1Y p.a.' in COLUMN_MAP
        assert '3Y p.a.' in COLUMN_MAP

    def test_column_map_values(self):
        """Should map to expected display names"""
        assert COLUMN_MAP['1M'] == '1 Mth'
        assert COLUMN_MAP['3M'] == '3 Mth'
        assert COLUMN_MAP['1Y p.a.'] == '1 Yr pa'
        assert COLUMN_MAP['3Y p.a.'] == '3 Yr pa'
