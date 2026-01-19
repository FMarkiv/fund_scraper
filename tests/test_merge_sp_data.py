"""
Unit tests for merge_sp_data.py
"""

import pytest
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from merge_sp_data import parse_pct, match_filename, FILENAME_MAP


class TestParsePct:
    """Tests for parse_pct function"""

    def test_parse_float(self):
        """Should return float as-is"""
        assert parse_pct(5.5) == 5.5
        assert parse_pct(-3.2) == -3.2
        assert parse_pct(0.0) == 0.0

    def test_parse_integer(self):
        """Should return integer as-is"""
        assert parse_pct(5) == 5
        assert parse_pct(-3) == -3

    def test_parse_percentage_string(self):
        """Should parse percentage strings"""
        assert parse_pct("5.5%") == 5.5
        assert parse_pct("-3.2%") == -3.2
        assert parse_pct("10%") == 10.0

    def test_parse_string_without_percent(self):
        """Should parse numeric strings"""
        assert parse_pct("5.5") == 5.5
        assert parse_pct("-3.2") == -3.2

    def test_parse_none(self):
        """Should return None for None input"""
        assert parse_pct(None) is None

    def test_parse_nan(self):
        """Should return None for NaN"""
        assert parse_pct(pd.NA) is None
        assert parse_pct(float('nan')) is None

    def test_parse_with_whitespace(self):
        """Should handle whitespace"""
        assert parse_pct("  5.5%  ") == 5.5
        assert parse_pct(" 10 ") == 10.0


class TestMatchFilename:
    """Tests for match_filename function"""

    def test_asx_200(self):
        """Should match ASX 200 files"""
        assert match_filename("fs-sp-asx-200 nov-2025.pdf") == "S&P/ASX 200 Accumulation"
        assert match_filename("asx-200.pdf") == "S&P/ASX 200 Accumulation"

    def test_energy_sector(self):
        """Should match energy sector"""
        result = match_filename("fs-sp-asx-200-energy-sector-gics-nov-2025.pdf")
        assert result == "S&P/ASX 200 Energy Accumulation"

    def test_materials_sector(self):
        """Should match materials sector"""
        result = match_filename("fs-sp-asx-200-materials-sector-nov-2025.pdf")
        assert result == "S&P/ASX 200 Materials Accumulation"

    def test_health_care(self):
        """Should match health care sector"""
        result = match_filename("fs-sp-asx-200-health-care-nov-2025.pdf")
        assert result == "S&P/ASX 200 HealthCare Accumulation"

    def test_financials(self):
        """Should match financials (fin-x-prop) correctly"""
        result = match_filename("fs-sp-asx-200-financial-x-a-reit-nov-2025.pdf")
        assert result == "S&P/ASX 200 Fin-x-Prop Accumulation"

    def test_a_reit(self):
        """Should match A-REIT sector"""
        result = match_filename("fs-sp-asx-200-a-reit-sector-nov-2025.pdf")
        assert result == "S&P/ASX 200 A-REIT Accumulation"

    def test_small_ordinaries(self):
        """Should match Small Ordinaries"""
        result = match_filename("fs-sp-asx-small-ordinaries-nov-2025.pdf")
        assert result == "S&P/ASX Small Ords Accumulation"

    def test_midcap_50(self):
        """Should match Midcap 50"""
        result = match_filename("fs-sp-asx-midcap-50-nov-2025.pdf")
        assert result == "S&P/ASX Midcap 50 Accumulation"

    def test_emerging_companies(self):
        """Should match Emerging Companies"""
        result = match_filename("fs-sp-asx-emerging-companies-nov-2025.pdf")
        assert result == "S&P/ASX Emerging Companies Accumulation"

    def test_gold_index(self):
        """Should match All Ordinaries Gold"""
        result = match_filename("fs-sp-asx-all-ordinaries-gold-nov-2025.pdf")
        assert result == "S&P/ASX All Ordinaries Gold Accumulation"

    def test_consumer_discretionary(self):
        """Should match Consumer Discretionary"""
        result = match_filename("fs-sp-asx-200-consumer-discretionary-nov-2025.pdf")
        assert result == "S&P/ASX 200 Discretion Accumulation"

    def test_consumer_staples(self):
        """Should match Consumer Staples"""
        result = match_filename("fs-sp-asx-200-consumer-staples-nov-2025.pdf")
        assert result == "S&P/ASX 200 Staples Accumulation"

    def test_communication_services(self):
        """Should match Communication Services / Telecoms"""
        result = match_filename("fs-sp-asx-200-communication-services-nov-2025.pdf")
        assert result == "S&P/ASX 200 Telecoms Accumulation"

    def test_information_technology(self):
        """Should match Information Technology"""
        result = match_filename("fs-sp-asx-200-information-technology-nov-2025.pdf")
        assert result == "S&P/ASX 200 Info Tech Accumulation"

    def test_utilities(self):
        """Should match Utilities"""
        result = match_filename("fs-sp-asx-200-utilities-sector-nov-2025.pdf")
        assert result == "S&P/ASX 200 Utilities Accumulation"

    def test_industrials(self):
        """Should match Industrials"""
        result = match_filename("fs-sp-asx-200-industrial-nov-2025.pdf")
        assert result == "S&P/ASX 200 Industrial Accumulation"

    def test_unmapped_filename(self):
        """Should return None for unmapped filenames"""
        assert match_filename("random-file.pdf") is None
        assert match_filename("unknown-index.pdf") is None

    def test_case_insensitive(self):
        """Should be case insensitive"""
        assert match_filename("ENERGY-SECTOR.pdf") == "S&P/ASX 200 Energy Accumulation"
        assert match_filename("Health-Care.pdf") == "S&P/ASX 200 HealthCare Accumulation"

    def test_financial_before_reit(self):
        """Financial-x-a-reit should match before a-reit (specificity)"""
        # This tests that the FILENAME_MAP order is correct
        # More specific patterns should be checked first
        result1 = match_filename("financial-x-a-reit-file.pdf")
        result2 = match_filename("a-reit-sector-file.pdf")

        assert result1 == "S&P/ASX 200 Fin-x-Prop Accumulation"
        assert result2 == "S&P/ASX 200 A-REIT Accumulation"


class TestFilenameMapOrder:
    """Tests to verify FILENAME_MAP ordering is correct"""

    def test_specific_patterns_first(self):
        """More specific patterns should appear before generic ones"""
        # Find indices
        indices = {pattern: i for i, (pattern, _) in enumerate(FILENAME_MAP)}

        # financial-x-a-reit should come before a-reit
        assert indices['financial-x-a-reit'] < indices['a-reit-sector']

        # all-ordinaries-gold is specific, should be early
        assert indices['all-ordinaries-gold'] < indices.get('asx-200 ', float('inf'))

    def test_all_patterns_are_lowercase(self):
        """All patterns should be lowercase for case-insensitive matching"""
        for pattern, _ in FILENAME_MAP:
            assert pattern == pattern.lower(), f"Pattern '{pattern}' should be lowercase"

    def test_no_duplicate_patterns(self):
        """Should not have duplicate patterns"""
        patterns = [pattern for pattern, _ in FILENAME_MAP]
        assert len(patterns) == len(set(patterns)), "Duplicate patterns found"

    def test_no_duplicate_fund_names(self):
        """Should not have duplicate fund names"""
        fund_names = [name for _, name in FILENAME_MAP]
        assert len(fund_names) == len(set(fund_names)), "Duplicate fund names found"
