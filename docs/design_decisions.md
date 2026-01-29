This project was intentionally designed to mimic real-world, high-volume event ingestion systems while keeping the scope focused on correctness, scalability, and analytics usability.

Each design choice reflects a trade-off, not an absolute rule.

# 1. Event-Driven Data Model (Core Decision)
## Decision
Model the system around events, not entities.

## Grain definition:
One row in the fact table = one GitHub event

## Why  
- GitHub is an event-producing system
- Events are immutable
- Event volume grows faster than dimensional data
- New event types appear frequently

## Benefit
- Schema evolution does not break pipelines
- Historical accuracy is preserved
- Scaling is linear with event volume

## Trade-off
- Some attributes are duplicated across events
- Requires downstream aggregation for business metrics

# 2. RAW Layer Accepts Chaos (No Cleaning)

## Decision
Store API responses exactly as received in the RAW layer.

## Why
- APIs evolve without warning
- Optional fields may appear or disappear
- Early cleaning can permanently lose information

## Benefit
- Full reprocessability
- Debugging and backfills are possible
- Original source of truth is preserved

## Trade-off
- RAW data is not analytics-friendly
- Querying RAW directly is intentionally painful

# 3. Bronze Layer Parses but Does Not Flatten
## Decision
Parse JSON into structured columns but retain nested structures.

## Why
- Not all nested fields are needed immediately
- Premature flattening increases schema rigidity
- Event-specific payloads vary by event type

## Benefit
- Schema evolution remains safe
- Future fields can be extracted without re-ingestion
- Supports incremental refinement

## Trade-off
- Bronze is not analyst-ready
- Requires a curated Silver layer

# 4. Silver Layer Defines the Contract
## Decision
Silver contains only stable, commonly queried attributes.

## Extracted:
- event_id
- event_type
- created_at
- actor_id
- repo_id
- event_date
- ingestion_time

## Why
- Analysts repeatedly query the same core fields
- Stable contracts prevent dashboard breakage
- Reduces repeated JSON parsing cost

## Benefit
- Predictable schema
- Fast joins
- Clear ownership of business meaning

## Trade-off
- Some flexibility is deferred to RAW
- Not all JSON fields are immediately accessible

# 5. Fact Table Before Dimensions
## Decision
Design the fact table first, then derive dimensions.

## Why
- Fact grain defines everything
- Dimensions only exist to describe facts
- Prevents over-modeling

## Benefit
- Correct joins
- No accidental grain mismatch
- Cleaner star schema

## Trade-off
- Requires upfront thinking
- Slower initial modeling

# 6. Business Keys in Dimensions (Not Surrogate Keys)
## Decision
Use natural/business keys:
- actor_id
- repo_id
- event_type

## Why
- GitHub already provides stable identifiers
- No Slowly Changing Dimension requirements
- Simplifies joins and debugging

## Benefit
- Transparent joins
- Easier traceability
- Lower storage overhead

## Trade-off
- Less flexibility if business keys change (unlikely here)

# 7. DATE over TIMESTAMP in Date Dimension
## Decision
Store event_date as DATE, not TIMESTAMP.

## Why
- Most analytics are date-based
- Time precision adds noise
- Simplifies grouping and partitioning

## Benefit
- Faster aggregations
- Cleaner queries
- Smaller dimension table

## Trade-off
- Hour-level analysis requires fact table access

# 8. Ingestion Time ≠ Event Time
## Decision
Store both:
- created_at → when event occurred
- ingestion_time → when system received it

## Why
- Late arrivals happen
- Reprocessing changes ingestion time
- Debugging data freshness requires separation

## Benefit
- Accurate latency analysis
- Correct backfills
- Operational observability

## Trade-off
- Extra column
- Slightly more modeling effort

# 9. ELT over ETL
## Decision
Load first, transform later.

## Why
- Snowflake handles compute scaling
- Semi-structured data support is strong
- Transform logic evolves faster than ingestion

## Benefit
- Faster onboarding of new data
- Easier reprocessing
- Clear separation of concerns

## Trade-off

- Requires warehouse discipline
- RAW data must be governed

# 10. - GOLD Tables Are Opinionated (By Design)
## Decision
Each GOLD table answers one specific question.

Examples:
- FACT_EVENTS_DAILY → trend analysis
- TOP_ACTIVE_USERS → engagement
- USER_RETENTION → stickiness
- REPO_ACTIVITY_CONCENTRATION → community health

## Why
- Metrics are opinions
- Dashboards need stable definitions
- Avoid repeated expensive joins

## Benefit
- BI-ready
- Faster dashboards
- Clear business meaning

## Trade-off
- Multiple tables instead of one
- Requires documentation

# 11. Activity Is Inferred, Not Explicit
## Decision
Define “active users” based on event presence, not flags.

## Why
- Event systems don’t track status
- Activity = participation
- Matches real behavioral analytics

## Benefit
- Works without additional metadata
- Scales naturally with event volume

## Trade-off
- Cannot distinguish passive users
- Interpretation must be documented

# 12. Tool-Agnostic Analytics Layer
## Decision
No BI-specific logic in pipelines.

## Why
- SQL should be the contract
- Avoid vendor lock-in
- Promote reusability

## Benefit
- Works with Power BI, Tableau, Looker
- Direct warehouse access

## Trade-off
- Visualization logic lives outside pipeline

# Final Philosophy
“Growth breaks rigid schemas, not flexible systems.”

## This pipeline prioritizes:
- Event immutability
- Schema evolution
- Analytics usability
- Reprocessability

## Over:
- Premature optimization
- Over-cleaning
- Tool-specific design
