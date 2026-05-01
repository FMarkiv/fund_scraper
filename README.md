# Fund Scraper 

Automated system for Scrapeing fund performance data from InvestSmart, fetches commodity/crypto benchmarks, extracts S&P sector indices from PDFs, 


- **Web Scraping**: Automated Selenium-based scraping from InvestSmart.com.au
- **Benchmark Data**: Auto-fetches Gold, Silver, Bitcoin, Ethereum prices via yfinance
- **PDF Extraction**: Extracts S&P Global sector performance from PDF factsheets
- **Coverage Tracking**: Validates scraping success and tracks month-over-month changes

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fund_scraper.git
cd fund_scraper

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
fund_scraper/
├── fund_scraper.py        # Main InvestSmart web scraper
├── check_coverage.py      # Scrape validation tool
├── merge_sp_data.py       # S&P PDF data merger
├── index/
│   ├── pdfscraper.py      # S&P PDF factsheet extractor
│   ├── splinks.py         # S&P factsheet downloader
│   ├── sp_links.xlsx      # S&P index URLs
├── fund_config.xlsx       # Master fund configuration
├── fund_links.xlsx        # Fund URLs for scraping
├── manual_data.xlsx       # Manual data (CPI, GICS, Benchmarks)
└── requirements.txt       # Python dependencies
```

## Monthly Workflow

### Phase 1: Data Collection

#### Step 1: Scrape Fund Performance
```bash
python fund_scraper.py
```
- Scrapes all funds from `fund_links.xlsx`
- Outputs: `fund_performance_YYYYMMDD_HHMMSS.csv`
- Takes ~2-3 hours (rate-limited to avoid blocking)

#### Step 2: Download S&P Sector PDFs
```bash
cd index
python splinks.py
```
- Downloads factsheet PDFs from S&P Global
- Saves to `index/pdfs/` folder

#### Step 3: Extract S&P Data from PDFs
```bash
cd index
python pdfscraper.py
```
- Extracts Total Return data from page 2 of each PDF
- Outputs: `performance_data.csv`

#### Step 4: Merge S&P Data
```bash
python merge_sp_data.py
```
- Maps PDF filenames to fund names
- Updates `manual_data.xlsx` (GICS_Sectors sheet)

### Phase 2: table Generation

#### Step 1: Fetch Benchmark Prices
```bash
python fetch_benchmarks.py --date 2022-03-31
```
- Fetches Gold, Silver, BTC, ETH prices as of specified date
- Calculates 1M, 3M, 1Y, 3Y returns
- Outputs: `benchmark_data.csv`



#### Step 3: Generate Table (Preview)
```bash
python generate.py --month 2026-03 --preview
```
- Merges all data sources
- Generates HTML
- Opens in browser for review

#### Step 4: Generate Final 
```bash
python generate.py --month 2026-03
```
- Outputs: `final.html`
- Upload to website 

### Phase 3: Validation

#### Check Scraping Coverage
```bash
python check_coverage.py
```
- Shows which funds failed to scrape
- Lists missing URLs

#### Compare to Previous Month
```bash
python check_coverage.py --compare fund_performance_previous.csv
```
- Shows added/removed funds month-over-month

## Data Flow

```
fund_links.xlsx ──────────────────┐
                                  ▼
                         fund_scraper.py
                                  │
                                  ▼
                    fund_performance_YYYYMMDD.csv
                                  │
                                  ├──────────────────────┐
                                  ▼                      ▼
                         generate.py    check_coverage.py
                                  ▲
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
fund_config.xlsx          benchmark_data.csv       manual_data.xlsx
                                  ▲                       ▲
                                  │                       │
                         fetch_benchmarks.py      merge_sp_data.py
                                                          ▲
                                                          │
                                                  performance_data.csv
                                                          ▲
                                                          │
                                                   pdfscraper.py
                                                          ▲
                                                          │
                                                    index/pdfs/
                                                          ▲
                                                          │
                                                    splinks.py
```

## Configuration Files

### fund_config.xlsx
Master configuration with columns:
- `Fund Name`: Official fund name
- `Display Name`: Short name for newsletter
- `Asset Class`: Category (Fixed Income, Domestic Large Cap, etc.)
- `Is Benchmark`: True/False flag
- `Active`: Include in newsletter (True/False)

### fund_links.xlsx
Fund URLs with columns:
- `Fund Name`: Must match fund_config.xlsx
- `URL`: InvestSmart fund page URL

### manual_data.xlsx
Three sheets:
- `CPI_Benchmarks`: Australian CPI data (CPI, CPI+1%, CPI+2%, CPI+3%)
- `GICS_Sectors`: S&P sector data (auto-populated by merge_sp_data.py)
- `Other_Manual`: Fallback data for funds that can't be scraped


## Troubleshooting

### Scraper Issues
- **Modal popups**: Handled automatically, but may need CSS selector updates
- **Rate limiting**: Adjust `BATCH_SIZE`, `MIN_DELAY`, `MAX_DELAY` in fund_scraper.py
- **Missing tables**: Check XPath patterns if InvestSmart updates their layout

### Missing Data
- Run `check_coverage.py` to identify failed scrapes
- Add fallback data to `manual_data.xlsx` (Other_Manual sheet)
- Check `fund_report_YYYY_MM.txt` for stale/missing fund details

### PDF Extraction
- Ensure PDFs are from S&P Global with standard layout
- Check page 2 contains "Total Return" row
- Update `FILENAME_MAP` in merge_sp_data.py for new indices

## License

Private project - All rights reserved.
