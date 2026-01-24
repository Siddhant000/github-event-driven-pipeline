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

# Observations:

- Multiple event types (PushEvent, PullRequestEvent, WatchEvent, etc.)
- Deeply nested JSON structures
- Fields that appear only for specific event types
- Optional and missing fields
- JSON returned as an array, not newline-delimited records

Key Question:

  “Can this data be directly stored in a relational table?”
Answer: ❌ No
Schema instability would break downstream analytics.
