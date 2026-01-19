# Fund Scraper & Newsletter Generator

Automated system for generating monthly financial newsletters for Australian investment funds. Scrapes fund performance data from InvestSmart, fetches commodity/crypto benchmarks, extracts S&P sector indices from PDFs, and generates professional HTML newsletters.

## Features

- **Web Scraping**: Automated Selenium-based scraping from InvestSmart.com.au
- **Benchmark Data**: Auto-fetches Gold, Silver, Bitcoin, Ethereum prices via yfinance
- **PDF Extraction**: Extracts S&P Global sector performance from PDF factsheets
- **Newsletter Generation**: Produces responsive HTML newsletters with sortable tables
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
├── generate_newsletter.py # HTML newsletter generator
├── fetch_benchmarks.py    # Gold/Silver/BTC/ETH price fetcher
├── check_coverage.py      # Scrape validation tool
├── merge_sp_data.py       # S&P PDF data merger
├── index/
│   ├── pdfscraper.py      # S&P PDF factsheet extractor
│   ├── splinks.py         # S&P factsheet downloader
│   ├── sp_links.xlsx      # S&P index URLs
│   └── gics_links.xlsx    # GICS sector URLs
├── fund_config.xlsx       # Master fund configuration
├── fund_links.xlsx        # Fund URLs for scraping
├── manual_data.xlsx       # Manual data (CPI, GICS, crypto)
├── commentary.md          # Newsletter commentary template
└── requirements.txt       # Python dependencies
```

## Monthly Workflow

### Phase 1: Data Collection (Day Before Newsletter)

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

### Phase 2: Newsletter Generation (Newsletter Day)

#### Step 1: Fetch Benchmark Prices
```bash
python fetch_benchmarks.py --date 2025-11-30
```
- Fetches Gold, Silver, BTC, ETH prices as of specified date
- Calculates 1M, 3M, 1Y, 3Y returns
- Outputs: `benchmark_data.csv`

#### Step 2: Write Commentary
Edit `commentary.md` with your market insights for each asset class:
```markdown
## Fixed Income
[Your commentary here...]

## Domestic Large Cap
[Your commentary here...]

## Thought of the Month
[Your essay here...]
```

#### Step 3: Generate Newsletter (Preview)
```bash
python generate_newsletter.py --month 2025-11 --preview
```
- Merges all data sources
- Generates HTML newsletter
- Opens in browser for review

#### Step 4: Generate Final Newsletter
```bash
python generate_newsletter.py --month 2025-11
```
- Outputs: `newsletter_2025_11.html`
- Upload to website and email service (e.g., Beehiiv)

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
                         generate_newsletter.py    check_coverage.py
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

## Asset Classes

| Asset Class | Benchmark | Notes |
|-------------|-----------|-------|
| Fixed Income | CPI variants | Shows CPI outperformance stats |
| Private Credit | - | No benchmark comparison |
| Domestic Large Cap | S&P/ASX 200 | Shows % outperforming benchmark |
| Domestic Mid/Small Cap | S&P/ASX Small Ords | Dual benchmark support |
| Domestic Micro Cap | S&P/ASX Emerging | Shows % outperforming benchmark |
| International Equities | Various | Shows % outperforming benchmark |
| Infra + REITs | - | No benchmark legend |
| Other | Spot Gold | Gold-focused funds |
| GICS Sectors | S&P/ASX 200 | Includes 5Y and 10Y columns |
| Crypto | - | BTC, ETH benchmarks |

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
