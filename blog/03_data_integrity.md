# Data Integrity: The Case of the Missing Tackles

_Date: 14th of February 2026_

Building a football analytics platform isn't just about sophisticated similarity algorithms or shiny radar charts. It's about trust. If a user sees a Defensive Midfielder with "0.00 Tackles per 90", the trust in the entire platform evaporates no matter how accurate your xG model is.

This week, we went periodically through a "Deep Data Dive" to audit our metric integrity. Here is what we found, and why inspecting raw data is better than trusting documentation blindly.

## The Mystery of 0.00 Tackles

We noticed that elite defensive players like **João Palhinha** and **Declan Rice** were showing `0.0` or very low numbers for Tackling stats.

### The Assumption

In most football datasets, a `Tackle` is a top-level event. We assumed our ETL pipeline simply needed to filter for `event_type == 'Tackle'`.

### The Reality

StatsBomb data is highly granular. Upon inspecting the raw PostgreSQL tables:

```sql
SELECT type, attributes FROM event WHERE type = 'Duel' LIMIT 5;
```

We discovered that often, a Tackle isn't an event _type_. It's a subtype of a `Duel`. Or sometimes it's a `Foul`. Or an `Interception` that wasn't a pass.

We had to rewrite our `etl.py` to extract tackles from nested attributes:

```python
# Before
tackles = df[df['type'] == 'Tackle']

# After
unique_ids = set()
# 1. Explicit Tackles
unique_ids.update(df[df['type'] == 'Tackle']['id'])
# 2. Duels that resulted in a Tackle
unique_ids.update(df[
    (df['type'] == 'Duel') &
    (df['duel_type'] == 'Tackle')
]['id'])
```

## The "100/100" Creativity Problem

On the frontend, every midfielder looked like Kevin De Bruyne. Their "Creativity" and "Passing" scores were maxed out on the radar charts.

This wasn't a data extraction bug; it was a **Normalization** failure.

Our frontend was hardcoded to normalize metrics on a 0-1 scale, but the `max` value for `key_passes_per90` was set to `0.5`. In reality, top players average significantly more than that. By clamping the visualization too low, we lost the ability to distinguish "Good" from "Elite".

We adjusted the heuristic thresholds:

- **Key Passes Max**: Raised from 0.5 -> 3.5
- **Pressures Max**: Adjusted to 40.0

## Conclusion: Golden Master to the Rescue

We are now implementing **Golden Master Tests** (snapshot testing) on our raw SQL-to-Metric pipeline. By locking in the calculated stats for a known player (e.g., Kane's 2015 season), we ensure that future "optimizations" don't accidentally erase all his goals or assists.

Trust is hard to earn and easy to lose. Always audit your raw data.
