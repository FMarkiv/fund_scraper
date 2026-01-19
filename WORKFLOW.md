# Monthly Newsletter Workflow

Step-by-step process for generating the ausyield monthly newsletter.

---

## Timeline Overview

```
Month End (EOM)     EOM + 5-7 days      15th - 22nd         Same Day
     │                   │                   │                  │
     ▼                   ▼                   ▼                  ▼
┌─────────┐        ┌──────────┐        ┌──────────┐       ┌──────────┐
│ S&P PDFs│        │  Funds   │        │ Generate │       │ Publish  │
│Available│        │  Update  │        │Newsletter│       │          │
└─────────┘        └──────────┘        └──────────┘       └──────────┘
                   (InvestSmart)
```

**Typical Run Date:** 15th - 22nd of the month
- End of Month: ~15th (most funds updated)
- End of Quarter: ~20th-22nd (longer lag for quarterly reporters)

---

## Phase 1: Data Collection (Can Start at EOM)

### Step 1.1: Download S&P PDFs (Manual)
**When:** As soon as available after month-end
**Time:** ~10 minutes

1. Go to S&P Global website
2. Download each sector factsheet PDF
3. Save to `index/pdfs/` folder

**Files to download:**
- ASX 200
- All GICS sectors (Energy, Materials, Industrials, etc.)
- Small Ordinaries, Midcap 50, Emerging Companies
- All Ordinaries Gold

---

### Step 1.2: Extract S&P PDF Data
**When:** After PDFs downloaded
**Time:** ~1 minute

```bash
cd index
python pdfscraper.py
```

**Output:** `performance_data.csv`

---

### Step 1.3: Merge S&P Data
**When:** After PDF extraction
**Time:** ~1 minute

```bash
python merge_sp_data.py
```

**Output:** Updates `manual_data.xlsx` (GICS_Sectors sheet)

---

## Phase 2: Fund Scraping (15th - 22nd)

### Step 2.1: Run Fund Scraper
**When:** When most funds have updated (check a few key funds on InvestSmart first)
**Time:** ~2-3 hours (runs in background)

```bash
python fund_scraper.py
```

**Output:** `fund_performance_YYYYMMDD_HHMMSS.csv`

**Tips:**
- Run overnight or during lunch - it takes 2-3 hours
- Can resume if interrupted (already-scraped funds are saved)
- Check InvestSmart manually for a few key funds first to confirm they've updated

---

### Step 2.2: Check Coverage
**When:** After scraping completes
**Time:** ~1 minute

```bash
python check_coverage.py
```

**Review output for:**
- Failed scrapes (may need manual data entry)
- Funds with stale dates (not yet updated)

---

## Phase 3: Newsletter Generation (Same Day as Scraping)

### Step 3.1: Fetch Benchmark Data
**When:** After scraping
**Time:** ~1 minute

```bash
python fetch_benchmarks.py --date YYYY-MM-DD
```

Use the last day of the target month (e.g., `--date 2025-01-31` for January newsletter).

**Output:** `benchmark_data.csv`

---

### Step 3.2: Reset & Write Commentary
**When:** After reviewing preview data
**Time:** 15-30 minutes

```bash
REM Reset to blank template
scripts\reset_commentary.bat

REM Generate preview with blank commentary first
python generate_newsletter.py --month YYYY-MM --preview

REM Review the data, then edit commentary.md
notepad commentary.md
```

Add your market insights to each section:

```markdown
## Fixed Income
[Your commentary on fixed income performance...]

## Domestic Large Cap
[Your commentary on large cap equities...]

## Thought of the Month
[Your monthly essay/insight...]
```

---

### Step 3.3: Generate Newsletter (Preview)
**When:** After all data ready
**Time:** ~1 minute

```bash
python generate_newsletter.py --month YYYY-MM --preview
```

- Opens in browser for review
- Check for missing data, formatting issues
- Review `fund_report_YYYY_MM.txt` for any problems

---

### Step 3.4: Generate Final Newsletter
**When:** After preview looks good
**Time:** ~1 minute

```bash
python generate_newsletter.py --month YYYY-MM
```

**Output:** `newsletter_YYYY_MM.html`

---

## Phase 4: Publishing

### Step 4.1: Update Website
**Time:** ~5 minutes

1. Open `newsletter_YYYY_MM.html`
2. Upload/update on ausyield.com.au
3. Update newsletter archive/index page if needed

---

### Step 4.2: Publish to Substack
**Time:** ~10 minutes

1. Create new post in Substack
2. Copy newsletter content (see tips below)
3. Preview and send

**Copy Tips:**
- Open the HTML file in browser
- Select all content (Ctrl+A)
- Copy (Ctrl+C)
- Paste into Substack editor (Ctrl+V)
- Tables should preserve formatting
- Review and adjust any formatting issues

---

### Step 4.3: Share on LinkedIn
**Time:** ~5 minutes

**Option A: Link Post (Quick)**
```
📊 January 2025 Market Update

Key highlights:
• [Top performing asset class]
• [Notable fund movements]
• [Key insight from commentary]

Full newsletter: [ausyield.com.au link]

#investing #australia #markets #asxstocks
```

**Option B: Article Post (More Engagement)**
1. LinkedIn > Write Article
2. Copy "Thought of the Month" section as article body
3. Add link to full newsletter at end
4. Better for long-form insights

---

## Quick Reference Checklist

```
□ Phase 1: Data Collection (EOM)
  □ Download S&P PDFs manually
  □ Run: python index/pdfscraper.py
  □ Run: python merge_sp_data.py

□ Phase 2: Fund Scraping (15th-22nd)
  □ Check key funds on InvestSmart have updated
  □ Run: python fund_scraper.py
  □ Run: python check_coverage.py

□ Phase 3: Newsletter Generation
  □ Run: python fetch_benchmarks.py --date YYYY-MM-DD
  □ Edit commentary.md
  □ Run: python generate_newsletter.py --month YYYY-MM --preview
  □ Run: python generate_newsletter.py --month YYYY-MM

□ Phase 4: Publishing
  □ Upload to ausyield.com.au
  □ Post to Substack
  □ Share on LinkedIn
```

---

## Speeding Up the Process

### Current Bottlenecks & Solutions

| Bottleneck | Current Time | Suggestion |
|------------|--------------|------------|
| Fund scraping | 2-3 hours | Run overnight with Task Scheduler (see below) |
| S&P PDF downloads | 10 min manual | Create bookmark folder with all PDF links |
| Copying to Substack | 10 min | Consider Substack API integration |
| LinkedIn posting | 5 min | Use scheduling tool (Buffer, Hootsuite) |

### Automation Ideas

**1. Scheduled Scraping (Windows Task Scheduler)**

Create `run_scraper.bat`:
```batch
@echo off
cd C:\fund_scraper
python fund_scraper.py
python check_coverage.py > coverage_report.txt
```

Schedule to run overnight on the 16th of each month.

**2. One-Command Newsletter Generation**

Create `generate.bat`:
```batch
@echo off
cd C:\fund_scraper
python fetch_benchmarks.py --date %1
python generate_newsletter.py --month %2 --preview
```

Usage: `generate.bat 2025-01-31 2025-01`

**3. S&P PDF Bookmarks**

Create a browser bookmark folder with direct links to each S&P factsheet. Open all at once, download folder set to `index/pdfs/`.

**4. LinkedIn Scheduling**

Draft LinkedIn posts in advance using a template. Schedule via:
- LinkedIn's native scheduler (free)
- Buffer (free tier available)
- Hootsuite

---

## Troubleshooting

### Scraper Failures
```bash
# Check what failed
python check_coverage.py

# For failed funds, add manual data to manual_data.xlsx (Other_Manual sheet)
```

### Stale Data Warning
If funds show old dates in the report:
- Wait a few more days for them to update
- Or exclude from this month's newsletter
- The generator automatically filters stale data

### Missing Benchmarks
```bash
# Re-run with explicit date
python fetch_benchmarks.py --date 2025-01-31

# Check yfinance is working
python -c "import yfinance as yf; print(yf.download('GC=F', period='5d'))"
```

---

## Monthly Calendar Template

```
1st-5th:    S&P PDFs available → Download and extract
5th-14th:   Wait for funds to update on InvestSmart
15th-18th:  [End of Month] Run scraper, generate newsletter
20th-22nd:  [End of Quarter] Run scraper, generate newsletter
Same day:   Publish to website, Substack, LinkedIn
```
