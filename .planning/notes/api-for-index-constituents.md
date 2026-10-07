---
title: "API Selection for Index Constituents"
date: "2026-10-07"
context: "Exploration session to automate index constituents updates."
---

# API Selection for Index Constituents

We decided to use an authenticated free API over keyless Wikipedia scraping to guarantee reliable coverage of massive indices like the Russell 2000. 

While scraping Wikipedia is a common strategy for indices like the S&P 500, it breaks down for larger, frequently rebalanced indices like the Russell 2000 which Wikipedia does not host in full. Financial Modeling Prep (FMP) and Finnhub provide index constituent endpoints on their free-tier APIs and thus were selected for the automated fortnightly GitHub Action updates.

*   **Admitted**: Wikipedia reliably hosts constituent tables for S&P 500, NASDAQ, Dow Jones, FTSE 100, Nikkei 225. [admit: wikipedia.org]
*   **Admitted**: Russell 2000 does NOT have a full constituent list on Wikipedia due to size. [admit: wikipedia.org]
*   **Admitted**: FMP and Finnhub provide free-tier index constituents. [admit: financialmodelingprep.com, finnhub.io]
*   **Unresolved**: Extracting via Yahoo Finance `yfinance` library. [abstain: scraper stability is unverifiable, frequently breaks without warning]
