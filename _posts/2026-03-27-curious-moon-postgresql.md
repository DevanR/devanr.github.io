---
layout: post
title: "Learning PostgreSQL with NASA's Cassini Data: A Curious Moon"
excerpt: ""
categories: articles
tags: [postgresql, sql, nasa, cassini, enceladus, data-analysis]
share: true
comments: false
modified:
---

I recently worked through _A Curious Moon_ by Rob Conery, a PostgreSQL tutorial with a twist: instead of contrived examples, you analyse real data from NASA's Cassini spacecraft mission to Saturn's moon Enceladus. Here are the features and concepts that stood out.

## The Setup

Enceladus is one of the most scientifically interesting moons in our solar system -- water geysers erupt from its south pole, hinting at a subsurface ocean. The Cassini spacecraft flew past it 23 times between 2005 and 2015, collecting gigabytes of instrument data. That data is publicly available from NASA's Planetary Data System, and this book has you import and analyse it with PostgreSQL.

The datasets include:

- **Master Plan** -- the full Cassini mission timeline of events and observations
- **INMS** -- Ion and Neutral Mass Spectrometer readings (1.3GB, 3.3 million rows)
- **CDA** -- Cosmic Dust Analyzer impact events (57,000 dust particle detections)

## What Makes It Interesting

### Real Data, Real Problems

Scientific data is messy. Columns use sentinel values like `-99.99` for missing readings. Some rows are truncated. Headers repeat mid-file. The book doesn't shy away from this -- you learn to handle it because you have to.

### Full Text Search for Science

One of the more satisfying chapters uses PostgreSQL's built-in full text search (`tsvector`, `tsquery`) to search through Cassini's mission plan descriptions. Instead of chaining `LIKE` and `ILIKE` queries, you build a proper search index and query it:

```sql
select * from events
where to_tsvector(description) @@ to_tsquery('enceladus & plume');
```

### Window Functions with Purpose

Window functions can feel abstract in a textbook. Here, they answer real questions -- calculating running counts of dust impacts, partitioning flyby data by time windows, and computing altitude changes during closest approach. The context makes the syntax stick.

### CTEs That Build on Each Other

The later chapters chain multiple CTEs together to solve complex analytical problems. For example, finding the exact moment of closest approach during each flyby requires finding the minimum altitude per week, joining back to get timestamps, then building time windows around those moments:

```sql
with mins as (
  select min(altitude) as nadir, year, week
  from time_altitudes
  group by year, week
), min_times as (
  select mins.*,
    min(time_stamp) as low_time,
    min(time_stamp) + make_interval(secs => 20) as window_end,
    min(time_stamp) - make_interval(secs => 20) as window_start
  from mins
  inner join time_altitudes ta
  on mins.year = ta.year and mins.week = ta.week
  and mins.nadir = ta.altitude
  group by mins.week, mins.year, mins.nadir
)
select * from min_times;
```

### Progressive Database Design

The book mirrors how database design actually evolves. You start with a flat CSV import into text columns, normalise into proper types with foreign keys, create views for convenience, add indexes when queries get slow, and refactor tables as your understanding deepens. It's not a clean top-down design -- it's iterative, which feels honest.

## Chapter Progression

1. **Database setup** -- schemas, COPY imports, basic type casting
2. **Normalisation** -- lookup tables, foreign keys, data integrity
3. **Finding flybys** -- pattern matching, regex, joins across tables
4. **Full text search** -- views, tsvector/tsquery, date ranges
5. **INMS analysis** -- date/time functions, CTEs, aggregations
6. **Dust analysis** -- window functions, materialized views, custom functions
7. **Gravity assist** -- complex multi-stage CTEs, interval arithmetic
8. **Under the ice** -- chemical analysis, time-window joins, index optimisation

## Worth It?

If you already know basic SQL and want to get comfortable with PostgreSQL's more powerful features -- CTEs, window functions, full text search, custom functions -- this is a compelling way to learn them. The scientific context keeps things interesting, and working with a genuinely large dataset (3.3 million INMS rows) forces you to care about performance in a way that toy examples never do.
