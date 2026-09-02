# Graph Report - .  (2026-08-07)

## Corpus Check
- Corpus is ~4,299 words - fits in a single context window. You may not need a graph.

## Summary
- 44 nodes · 63 edges · 5 communities
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- App & CLI Interface
- UMKM Data & Documentation
- Scraping Engine
- Phone Utils & WA Link
- Browser Driver & Detail

## God Nodes (most connected - your core abstractions)
1. `UMKMScraper` - 10 edges
2. `UMKM Scraper & Lead Generator Indonesia` - 9 edges
3. `export_to_dataframe()` - 7 edges
4. `PhoneUtils` - 6 edges
5. `main()` - 3 edges
6. `ContactExtractor` - 3 edges
7. `Multi-Source Data Extraction` - 2 edges
8. `UMKM Scraper Web Dashboard - Streamlit Interactive UI Provides real-time…` - 1 edges
9. `UMKM Scraper CLI - Command Line Tool Run UMKM scraping directly from terminal…` - 1 edges
10. `UMKM Scraper Engine - Core Scraping & Contact Extraction Module Strategy:…` - 1 edges

## Surprising Connections (you probably didn't know these)
- `Bebek Ali Borme` --conceptually_related_to--> `UMKM Scraper & Lead Generator Indonesia`  [INFERRED]
  graphify-out/converted/umkm_result_dd65f087.md → README.md
- `Roemah Nenek` --conceptually_related_to--> `UMKM Scraper & Lead Generator Indonesia`  [INFERRED]
  graphify-out/converted/umkm_result_dd65f087.md → README.md
- `Sudirman Street Day and Night Market` --conceptually_related_to--> `UMKM Scraper & Lead Generator Indonesia`  [INFERRED]
  graphify-out/converted/umkm_result_dd65f087.md → README.md
- `Warung Nasi Ibu Imas` --conceptually_related_to--> `UMKM Scraper & Lead Generator Indonesia`  [INFERRED]
  graphify-out/converted/umkm_result_dd65f087.md → README.md
- `Yoghurt Cisangkuy` --conceptually_related_to--> `UMKM Scraper & Lead Generator Indonesia`  [INFERRED]
  graphify-out/converted/umkm_result_dd65f087.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Scraped Indonesian UMKM Data Entries** — graphify_out_converted_umkm_result_dd65f087_sudirman_street_market, graphify_out_converted_umkm_result_dd65f087_bebek_ali_borme, graphify_out_converted_umkm_result_dd65f087_roemah_nenek, graphify_out_converted_umkm_result_dd65f087_warung_nasi_ibu_imas, graphify_out_converted_umkm_result_dd65f087_yoghurt_cisangkuy [EXTRACTED 1.00]

## Communities (5 total, 0 thin omitted)

### Community 0 - "App & CLI Interface"
Cohesion: 0.24
Nodes (7): UMKM Scraper Web Dashboard - Streamlit Interactive UI Provides real-time…, main(), UMKM Scraper CLI - Command Line Tool Run UMKM scraping directly from terminal…, DataFrame, export_to_dataframe(), UMKM Scraper Engine - Core Scraping & Contact Extraction Module Strategy:…, Converts scraped list of dicts to a cleaned pandas DataFrame.

### Community 1 - "UMKM Data & Documentation"
Cohesion: 0.18
Nodes (11): Bebek Ali Borme, Roemah Nenek, Sudirman Street Day and Night Market, Warung Nasi Ibu Imas, Yoghurt Cisangkuy, CLI Terminal Interface, Deep Website Enrichment, Multi-Source Data Extraction (+3 more)

### Community 2 - "Scraping Engine"
Cohesion: 0.36
Nodes (5): Any, ContactExtractor, Extracts additional WhatsApp links, social profiles, and emails from target…, Two-pass Google Maps scraper: Pass 1: Search → scroll → collect card names &…, Fast HTTP-based fallback scraper using Bing search.

### Community 3 - "Phone Utils & WA Link"
Cohesion: 0.38
Nodes (4): PhoneUtils, Helper class to clean, parse, and format Indonesian phone numbers and WA links., Formats a raw phone string. Returns: (phone_raw, phone_formatted, wa_link), Extracts potential Indonesian mobile / phone numbers from raw text or HTML.

### Community 4 - "Browser Driver & Detail"
Cohesion: 0.29
Nodes (4): Main Scraping Engine. Strategy: Pass 1 - Search Google Maps, scroll & collect…, Initializes Chrome or Edge WebDriver via Selenium with desktop resolution., Extracts business details from the currently open Google Maps detail panel.…, UMKMScraper

## Knowledge Gaps
- **7 isolated node(s):** `Streamlit Web Dashboard UI`, `CLI Terminal Interface`, `Sudirman Street Day and Night Market`, `Bebek Ali Borme`, `Roemah Nenek` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UMKMScraper` connect `Browser Driver & Detail` to `App & CLI Interface`, `Scraping Engine`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `PhoneUtils` connect `Phone Utils & WA Link` to `App & CLI Interface`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `export_to_dataframe()` connect `App & CLI Interface` to `Scraping Engine`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `UMKM Scraper & Lead Generator Indonesia` (e.g. with `Bebek Ali Borme` and `Roemah Nenek`) actually correct?**
  _`UMKM Scraper & Lead Generator Indonesia` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Streamlit Web Dashboard UI`, `CLI Terminal Interface`, `Sudirman Street Day and Night Market` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._