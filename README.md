🧠 Architecture Overview

This system is designed to analyze logs at scale without storing raw logs.
Instead of persisting massive log data, it focuses on rule-based signal extraction and periodic analysis (7-day window).

The core philosophy is:

Logs are transient.
Signals are persistent.
Analysis is the product.

```text
Application / OS
  └─ Log Stream (stdout / stderr / system)

        ↓

Log Agent Script (lightweight, local)
  - Near real-time ingestion
  - No database writes
  - No buffering of raw logs

        ↓  HTTP POST
           (with context headers)

Ingestion API
  - X-Tenant-ID
  - X-Project-ID
  - X-Agent-ID (optional)
  - Raw log lines (streamed)

        ↓  (in-memory processing)

Rule Engine
  - Deterministic rules
  - Pattern detection
  - Anomaly heuristics
  - Evidence generation (ephemeral)

        ↓  signal extraction

Signal Aggregator
  - Keyword-based signals
  - Count & severity aggregation
  - Time-windowed (daily / 7-day)

        ↓  persist (small & meaningful)

Analysis Storage
  - tenant_id
  - project_id
  - analysis period (e.g. 7 days)
  - aggregated signals only
  - NO raw logs stored

        ↓

Analysis & Reporting
  - 7-day trend analysis
  - Severity scoring
  - Optional GPT enrichment
  - Human-readable reports

```
