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

