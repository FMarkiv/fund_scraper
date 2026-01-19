
# AUSYIELD NEWSLETTER AUTOMATION - SETUP SUMMARY

## COVERAGE ACHIEVED: 94%

After fixes applied:
- 227 total funds in config
- 200 matched from scraped + manual data
- 23 manual entries (CPI, GICS, Gold, Crypto)
- 12 funds still need InvestSmart URLs

---

## FILES DELIVERED

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `fund_config.xlsx` | Master fund list | When adding funds |
| `fetch_benchmarks.py` | Auto-fetch Gold/Silver/BTC/ETH | Monthly |
| `manual_data.xlsx` | CPI + GICS sector data | CPI quarterly, GICS monthly |
| `commentary.md` | Your written commentary | Monthly |
| `generate_newsletter.py` | Generates HTML output | Never (just run it) |

---

## MONTHLY WORKFLOW

```
DAY BEFORE:
1. Run InvestSmart scraper → fund_performance_YYYYMMDD.csv
2. Run S&P PDF scraper → update GICS_Sectors in manual_data.xlsx

NEWSLETTER DAY:
1. python fetch_benchmarks.py --date 2025-11-30
2. python generate_newsletter.py --month 2025-11 --preview
3. Write commentary in commentary.md
4. python generate_newsletter.py --month 2025-11 --preview
5. Upload to site + Beehiiv
```

---

## 12 FUNDS STILL MISSING (need InvestSmart URLs)

These funds are in your config but weren't scraped. Add them to `fund_links.xlsx`:

| Fund Name | Likely Issue |
|-----------|--------------|
| AQLT - BetaShares Australian Quality ETF | ETF - may use different InvestSmart URL format |
| Australian Eagle Trust | May be delisted or renamed |
| Claremont Global Fund | Check InvestSmart listing |
| EX20 - Betashares Aus Ex-20 Portfolio Diversifier ETF | ETF URL format |
| Elstree Enhanced Income Fund | Check InvestSmart listing |
| MOAT- VanEck Morningstar Wide MOAT ETF | ETF URL format |
| Milford Dynamic Small Companies Fund | Check InvestSmart listing |
| Phoenix Growth Fund | Check InvestSmart listing |
| Regal Resources Long Short Fund - Class A Units | May have different class listed |
| Tectonic Opportunities Fund | Check InvestSmart listing |
| VanEck MSCI International Quality ETF (QUAL) | ETF URL format |
| VanEck MSCI International Small Cap Quality ETF (QSML) | ETF URL format |

**Note:** Many of these are ETFs which may have different URL patterns on InvestSmart.
Check: https://www.investsmart.com.au/investment-centre/etfs

---

## FIXES APPLIED TO fund_config.xlsx

1. **Whitespace stripped** from all fund names
2. **Name corrections:**
   - `Aquasia Short-Term Income Fund` → `Aquasia Short-term Income`
   - `Auscap High Conviction...` → `Auscap High Conviction... (Daily Platform Class)`
   - `MVOL - iShares Australia...` → `MVOL - iShares Edge MSCI Australia...`

3. **9 new funds added** from scraped data:
   - Blackwattle Mid Capital Quality (Domestic Mid/Small Cap)
   - Bronte Capital Amalthea Fund (Domestic Large Cap)
   - Capital Group New Perspective (AU) (Domestic Large Cap)
   - ECP Growth Companies (Domestic Large Cap)
   - MFS Global New Discovery Trust (International Equities)
   - MFS Global Opportunistic Fixed Income Trust (Fixed Income)
   - PM Capital Global Companies Fund (International Equities)
   - Partners Group Global Multi-Asset Fund (International Equities)
   - T. Rowe Price Global High Income (Fixed Income)

---

## DEPENDENCIES

Install before running:
```bash
pip install pandas openpyxl yfinance python-dateutil markdown
```

