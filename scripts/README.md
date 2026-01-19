# Automation Scripts

Batch files to automate the newsletter workflow.

## Quick Start

For a typical month-end run:

```batch
scripts\full_workflow.bat 2025-01-31 2025-01
```

## Individual Scripts

### `run_scraper.bat`
Runs the fund scraper and saves a coverage report. Schedule this with Windows Task Scheduler for overnight runs.

```batch
scripts\run_scraper.bat
```

**Schedule with Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Monthly, 16th at 11:00 PM
4. Action: Start a program
5. Program: `C:\fund_scraper\scripts\run_scraper.bat`

---

### `process_sp_pdfs.bat`
Processes S&P PDF factsheets after manual download.

```batch
scripts\process_sp_pdfs.bat
```

**Prerequisite:** Download PDFs to `index/pdfs/` first.

---

### `generate.bat`
Fetches benchmarks and generates the newsletter with preview.

```batch
scripts\generate.bat 2025-01-31 2025-01
```

**Arguments:**
- `2025-01-31` - End date for benchmark prices
- `2025-01` - Newsletter month

---

### `full_workflow.bat`
Runs the complete workflow: S&P processing → Scraping → Generation.

```batch
scripts\full_workflow.bat 2025-01-31 2025-01
```

Interactive prompts let you skip steps (e.g., skip scraper if already run).

---

### `linkedin_post.bat`
Generates a LinkedIn post template and opens in Notepad for editing.

```batch
scripts\linkedin_post.bat 2025-01
```

---

## Typical Monthly Workflow

```batch
REM 1. After downloading S&P PDFs (EOM)
scripts\process_sp_pdfs.bat

REM 2. Run scraper overnight (15th-22nd)
scripts\run_scraper.bat

REM 3. Generate newsletter
scripts\generate.bat 2025-01-31 2025-01

REM 4. Create LinkedIn post
scripts\linkedin_post.bat 2025-01
```

Or run everything at once:

```batch
scripts\full_workflow.bat 2025-01-31 2025-01
```
