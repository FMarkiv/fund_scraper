# Changelog

All notable changes to this project will be documented in this file.

## [1.0.2] - 2025-01-19

### Testing

#### New Test Suite
- **tests/test_generate_newsletter.py**: Unit tests for newsletter generation
  - `TestParsePercentage`: 11 tests for percentage parsing edge cases
  - `TestGetPreviousMonth`: 3 tests for date calculations
  - `TestMergeData`: 3 tests for data merging logic
  - `TestCalculateOutperformance`: 3 tests for benchmark comparison
  - `TestLoadCommentary`: 2 tests for markdown parsing
  - `TestCommentaryToHtml`: 3 tests for HTML conversion

- **tests/test_fetch_benchmarks.py**: Unit tests for benchmark fetching
  - `TestGetMonthEndDate`: 5 tests for month-end calculations
  - `TestGetPriceAtDate`: 6 tests for price lookup with fallbacks
  - `TestCalculateReturns`: 3 tests for return calculations
  - `TestGetLastMonthEnd`: 3 tests for date logic
  - `TestBenchmarksConfig`: 4 tests for configuration validation

- **tests/test_merge_sp_data.py**: Unit tests for S&P data merging
  - `TestParsePct`: 7 tests for percentage parsing
  - `TestMatchFilename`: 18 tests for filename-to-fund mapping
  - `TestFilenameMapOrder`: 4 tests for mapping order validation

#### Configuration
- **pytest.ini**: Pytest configuration with verbose output
- **requirements.txt**: Added pytest>=7.0.0 and pytest-cov>=4.0.0

---

## [1.0.1] - 2025-01-19

### Code Quality Improvements

#### Exception Handling
- **fund_scraper.py**: Replaced 8 bare `except:` clauses with specific `except NoSuchElementException:` exceptions
  - Pattern matching for fund/ETF performance tables (lines 73, 81, 89)
  - Table body extraction (line 135)
  - Date extraction patterns (lines 166, 174, 183, 196, 206)

- **generate_newsletter.py**: Changed bare `except:` to `except ValueError:` in `parse_percentage()` function (line 243)

#### File Encoding
- **generate_newsletter.py**: Added `encoding='utf-8'` to:
  - `load_commentary()` file read (line 204)
  - Report file write (line 1234)
  - Newsletter HTML write (line 1270)

- **index/pdfscraper.py**: Added `encoding='utf-8'` to CSV file write (line 83)

#### Cross-Platform Compatibility
- **generate_newsletter.py**: Changed `os.path.getctime` to `os.path.getmtime` in `load_performance_data()` (line 139)
  - `getctime` returns creation time on Windows but inode change time on Unix
  - `getmtime` (modification time) is consistent across platforms

- **check_coverage.py**: Changed `os.path.getctime` to `os.path.getmtime` in `get_latest_csv()` (line 21)

#### Import Organization
- **fund_scraper.py**: Moved `import re` to top of file (line 16)
  - Previously imported inside `extract_performance_data()` function

- **index/pdfscraper.py**: Moved `import csv` to top of file (line 5)
  - Previously imported inside `main()` function

#### API Reliability
- **fetch_benchmarks.py**: Enhanced `fetch_price_history()` with:
  - Retry logic with 3 attempts
  - Exponential backoff (1s, 2s, 4s delays between retries)
  - Better empty data handling (`data.empty` check)
  - Support for newer yfinance multi-index column format
  - Added `import time` for retry delays

### New Files
- **requirements.txt**: Added Python dependencies file
  - pandas>=1.5.0
  - openpyxl>=3.0.0
  - selenium>=4.0.0
  - webdriver-manager>=4.0.0
  - yfinance>=0.2.0
  - python-dateutil>=2.8.0
  - markdown>=3.4.0
  - pdfplumber>=0.9.0

- **.gitignore**: Added comprehensive Python gitignore
  - Standard Python ignores (pycache, venv, IDE settings)
  - Project-specific ignores (generated CSVs, HTMLs, PDFs)

- **README.md**: Added project documentation
  - Installation instructions
  - Project structure
  - Complete workflow guide
  - Data flow diagram
  - Troubleshooting tips

## [1.0.0] - 2025-01-19

### Initial Release
- **fund_scraper.py**: Selenium-based InvestSmart fund performance scraper
  - Batch processing with rate limiting
  - Multiple XPath patterns for fund/ETF tables
  - Modal popup handling
  - Progress saving and resume capability

- **generate_newsletter.py**: HTML newsletter generator
  - Multi-source data merging (scraped, manual, benchmarks)
  - CPI outperformance calculations
  - Benchmark comparison statistics
  - Responsive HTML with client-side sorting
  - Markdown commentary support

- **fetch_benchmarks.py**: Commodity/crypto benchmark fetcher
  - Gold, Silver, Bitcoin, Ethereum prices via yfinance
  - AUD currency conversion for USD assets
  - 1M, 3M, 1Y, 3Y return calculations

- **check_coverage.py**: Scraping validation tool
  - Failed scrape detection
  - Month-over-month comparison

- **merge_sp_data.py**: S&P PDF data merger
  - Filename to fund name mapping
  - GICS sector data integration

- **index/pdfscraper.py**: S&P PDF factsheet extractor
  - pdfplumber-based text extraction
  - Total Return row parsing

- **index/splinks.py**: S&P factsheet downloader
  - Selenium-based PDF downloads
  - Configurable download folder

### Configuration Files
- **fund_config.xlsx**: Master fund configuration (227 funds)
- **fund_links.xlsx**: InvestSmart URLs for scraping
- **manual_data.xlsx**: CPI benchmarks, GICS sectors, manual entries
- **commentary.md**: Newsletter commentary template
