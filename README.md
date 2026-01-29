# github-event-driven-pipeline


# Problem Statement

Modern platforms like GitHub, Netflix, and Amazon generate massive volumes of event data in real time.
This data is:

- JSON-based
- Highly nested
- Schema-evolving
- Event-type dependent
- Not analytics-friendly out of the box

Traditional batch systems choke when:
- JSON arrives as arrays instead of newline-delimited records
- Schemas evolve unexpectedly
- Optional fields appear/disappear
- Payload size explodes

# Architecture Overview

GitHub Public Events API
        |
        v
RAW Layer (JSON as-is)
        |
        v
BRONZE Layer (Parsed, schema-aware)
        |
        v
SILVER Layer (Curated core events)
        |
        v
GOLD Layer (Analytics-ready tables)

# STEP 0 — Understand the Data (Before Writing Pipelines)
Before building pipelines, the API response was inspected manually.

## Observations:

- Multiple event types (PushEvent, PullRequestEvent, WatchEvent, etc.)
- Deeply nested JSON structures
- Fields that appear only for specific event types
- Optional and missing fields
- JSON returned as an array, not newline-delimited records

Key Question:

  “Can this data be directly stored in a relational table?”
Answer: ❌ No
Schema instability would break downstream analytics.

# STEP 1 — RAW Ingestion (Naive on Purpose)
What was done:
- Pulled data from GitHub Public Events API
- Stored the response exactly as received
- No flattening
- No cleaning
- No schema enforcement
- Partitioned by ingestion date

Why this matters:
- Preserves original data for reprocessing
- Prevents data loss
- Mirrors real ingestion systems
- RAW layer accepts chaos by design.

# STEP 2 — Pain Points Observed

Before optimization, several issues were observed:

- Files grow quickly
- Highly repetitive fields
- Nested structures are hard to query
- Different event types have different payload shapes
- Schema evolution can silently break analytics

These pains define the problem statement, not failures.

# STEP 3 — Event-Driven Thinking (Mindset Shift)

Instead of thinking in tables, the system was designed around events.

Definition:
        One event = one JSON object

Event Structure:
- Core metadata (stable)
- event_id
- event_type
- created_at
- actor
- repo
Payload (event-specific, unstable)

This separation allows schema evolution without breaking pipelines.

# STEP 4 — Spark Ingestion Challenges & Resolutions
❌ Issue 1: Spark Failed to Read JSON

Reason:
GitHub API returns JSON as a multi-object array, while Spark expects newline-delimited JSON.

Resolution:

        .option("multiLine", "true")

Why this matters:

Real APIs rarely produce analytics-friendly formats.

Issue 2: _corrupt_record Query Error

Spark disallows lazy queries that reference only _corrupt_record.

Resolution:

- Cache the parsed DataFrame
- Force materialization before inspection

        df.cache()
        df.count()

Learning:

Spark enforces schema integrity to avoid misleading results.

Issue 3: DBFS Disabled

Public DBFS access is restricted in modern Databricks workspaces.

Resolution:
- Used Unity Catalog Volumes instead

        /Volumes/<catalog>/<schema>/<volume>/

Benefit:
- Better security
- Production-aligned storage
- Governance-ready

# STEP 5 — Bronze Layer (Parsed, Not Flattened)

Data types are intentionally preserved as inferred from source to prevent schema rigidity and support evolution.

At the Bronze stage:

- JSON is parsed successfully
- Nested structures are preserved
- No transformations applied
- No business logic enforced

This layer ensures:

- Schema stability
- Reprocessability
- Observability of malformed data

The Bronze layer is stored using Delta Lake, providing ACID guarantees, schema evolution support, and columnar storage for scalable analytics.

# STEP 6 — Load into Snowflake (RAW schema)
Once the curated SILVER layer was finalized, data was loaded into Snowflake.

Design choices:

- Snowflake used as the analytical warehouse
- RAW schema accepts semi-structured data
- No aggressive cleaning at this stage
- Schema evolution allowed

Why Snowflake:

- Separation of storage and compute
- Excellent support for semi-structured data
- Scales independently for concurrent analytic
- ELT-friendly (transform after loading)

Goal:
“Prove that growing, messy event data can be ingested safely without breaking.”

# STEP 7 — SILVER to GOLD: Transformation & Optimization

At this stage, the focus shifts from data correctness to data usability.

Guiding questions:

- What will analysts query most?
- What metrics are repeatedly computed?
- Which joins are expensive and repetitive?
- What needs to be fast?

Instead of forcing analysts to work on raw facts, business-ready aggregates were created.

## GOLD Layer — Analytics-Ready Tables

The GOLD layer represents opinionated, purpose-built datasets.

Each table:

- Answers a specific analytical question
- Avoids complex joins
- Is dashboard-ready
- Can scale independently

1. FACT_EVENTS_DAILY

Purpose: Daily activity trend analysis

What it answers:

- How platform activity changes over time
- Growth or decline patterns
- Spikes caused by releases or incidents

Why important:

- Time-series analysis is the first question business asks
- Reduces repeated aggregations on raw events

2. PEAK_ACTIVITY_PER_DAY

Purpose: Identify busiest hours per day

What it answers:

- When users are most active
- Load patterns across time
- Optimal scheduling windows

Why important:

- Helps capacity planning
- Reveals user behavior patterns
- Useful for alerting and monitoring use cases

3. TOP_ACTIVE_USERS

Purpose: Identify highly engaged contributors

What it answers:

- Who generates the most activity
- Power users vs casual users
- Bots vs real users

Design note:

- “Active” is inferred from event presence, not a status flag
- In event-driven systems, activity = event creation

Why important:

- Engagement metrics are core business KPIs
- No explicit “active/inactive” column exists in raw data

4. USER_RETENTION

Purpose: Measure repeated user participation across days

What it answers:

- Do users come back?
- Are contributors one-time or recurring?
- Community stickiness

Why important:

- Retention is more meaningful than raw activity
- Distinguishes viral spikes from healthy ecosystems

5. EVENT_PER_REPO

Purpose: Repository popularity & usage patterns

What it answers:

- Which repositories attract activity
- What types of events dominate per repo
- Code vs issue vs CI behavior

Why important:

- Helps prioritize repositories
- Enables repo-level comparisons

6. REPO_ACTIVITY_CONCENTRATION

Purpose: Community health analysis

Logic:

- Compare total events vs unique contributors
- Detect whether activity is:
- Concentrated among few users
- Spread across many contributors

Interpretation:

- High concentration → Risky dependency on few users
- Healthy community → Balanced contribution
- Inactive → Low engagement

Why important:

- Raw counts hide participation imbalance
- This metric adds qualitative insight, not just volume

# STEP 8 — Growth-Aware Design Decisions

Several design decisions were made anticipating scale:

- Event-based grain avoids duplication
- Dimensions decouple slowly changing attributes
- GOLD tables reduce compute-heavy queries
- Semi-structured fields preserved until necessary
- Ingestion time stored separately from event time

Key realization:
Growth breaks rigid schemas, not flexible ones.

# STEP 9 — Analytics Readiness (Without BI Lock-in)

The GOLD layer is:

- Tool-agnostic
- Queryable directly in SQL
- Compatible with Power BI, Tableau, Looker
- Dashboards can be built without modifying pipelines.


# Final Key Takeaways

- Event-driven thinking simplifies schema evolution
- RAW ≠ useless; it is insurance
- Bronze is about correctness, not beauty
- Silver defines the contract
- Gold defines business truth
- Metrics are opinions — document them

# Data Modeling (Star Schema)
-  Fact Table
   Grain: One row per GitHub event
        
        fact_github_events:
        event_id
        event_type
        actor_id
        repo_id
        event_date
        ingestion_time

- Dimension Tables
  
- DIM_ACTOR:
  
        actor_id (PK)
        actor_login
        actor_type (User / Bot)

- DIM_REPO:
  
        repo_id (PK)
        repo_name
        repo_url
        owner_name

- DIM_EVENT_TYPE

        event_type (PK)
        category (code / issue / release / CI)

- DIM_DATE

        date_key (DATE)
        year, quarter, month, week
        day_name
        is_weekend

- Design principle:

- FACT uses event_id
- DIMs use business keys
- No event_id in dimensions

# Key Learnings

- Delta Lake = Parquet + transaction log
- ELT scales better for analytics workloads
- Snowflake prefers pull-based ingestion
- Dimension grain definition is critical
- DATE is superior to TIMESTAMP in date dimensions
- Semi-structured data should stay semi-structured until needed
