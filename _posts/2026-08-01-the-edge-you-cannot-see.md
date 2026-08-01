---
layout: post
title: "The Edge You Cannot See"
excerpt: "Both environments were serving through a new load balancer, and all four backend services had been writing zero logs since the day they were applied. Nobody turned logging off. That was the problem."
categories: articles
tags: [observability, load-balancing, gcp, infrastructure, opentofu, terraform]
comments: false
share: true
modified:
series: "Building it dark"
series_part: 6
---

The phase was finished. Both environments served through a same-origin HTTPS load
balancer, dark, on parallel hostnames, validated end to end.

Then someone asked where the edge logs were.

There weren't any. A backend service writes no request logs unless logging is
explicitly enabled, and the API default is *off*. All four backend services — two
per environment — had been silently unobservable since the day they were applied.

I checked live before writing a single line of the fix. Four out of four, logging
disabled. Nobody had turned it off. That is exactly what made it interesting.

## Why it mattered more than "we should have logs"

My first instinct was that this was mostly cosmetic. The container platform keeps
its own request log, so anything that *reaches* a service is already recorded,
with status, latency and URL. We weren't blind.

That instinct was wrong, and the reason is worth internalising.

What was missing is everything the load balancer handles **itself**:

- a request rejected by the WAF policy
- a 502 from a backend that never came up
- a request matching no path rule at all

None of those reach a service. So they leave no trace anywhere. Not in the
application logs, not in the platform's request log, nowhere.

They are also, by some distance, the failures hardest to reason about from a user
report. "It was down for me for about a minute" against a platform log showing an
uninterrupted stream of 200s is an unfalsifiable conversation. You cannot prove a
negative from an absence of evidence you created yourself.

And they get considerably more likely at cutover — the moment the edge stops being
dark and starts carrying every customer, which is the worst possible time to
discover you have no visibility at the one layer that's new.

## Three design calls worth stealing

The fix was small. The decisions inside it were the useful part.

**Default on, deliberately.** The new toggle defaults to enabled. I thought about
this for longer than the code took, because "default off, opt in per environment"
is the more conventional shape for anything that costs money.

The argument that settled it: *the failure mode we're fixing was reached by nobody
deciding anything.* No one weighed the cost of edge logs and chose to skip them.
The state arrived by omission. An edge that cannot be observed should not be a
state you can arrive at without a decision — so the default has to be the safe
value, and turning it off has to be a thing someone writes down and justifies.

Generalise it: **make the value you get when nobody thinks about it the value you
would have chosen if they had.**

**A sample rate, not an on/off switch.** Full sampling while the edge is dark:
volume is negligible, and a partial sample is worse than useless when you're
chasing one specific request a tester reported by timestamp.

But the knob exists so that at cutover, when volume is real and someone says "this
is getting expensive," the available answer is *sample down* — not *switch off and
lose the failure paths entirely*. If your only control is a boolean, cost pressure
will eventually find the off switch. Give the future a dial.

**Derive coupled fields together.** The API rejects a non-zero sample rate on a
disabled logging config. If you pass both values through independently, a caller
can construct that invalid pair and discover it at apply time, halfway through a
change.

Deriving both from one local — disabled forces the rate to zero — means the
invalid combination cannot be expressed. Make the illegal state unrepresentable,
in Terraform as much as in a type system.

There's a fourth, smaller one: both backends always share a single sample rate,
enforced by a test. A configuration where the web app logs and the API doesn't is
*worse* than neither logging, because a half-covered dashboard reads as complete
coverage. Partial observability lies more convincingly than none.

## The websocket footnote

Worth knowing before it confuses you at 2am: a websocket is **one** log entry,
written when the connection *closes*, with the entire connection lifetime recorded
as its latency.

That's good news for cost — one entry per connection, not per frame — and mildly
alarming the first time you tail the logs during a live session and see nothing at
all. The entries lag by however long the socket stays open. A quiet log is not
evidence of a quiet system.

## The module had no tests

The reusable edge module shipped without a single test. It now has six, and one of
them is the one I'd fight to keep.

Five assert the logging contract: on by default at full sampling, both backends
always sharing one rate, disabling forces the rate to zero, out-of-range rates
rejected at both ends.

The sixth asserts something the other five never mention — the routing invariant.
Only the API prefix and the socket path are carved out; everything else defaults to
the web app. That's the assumption the logging assertions quietly stand on. If
someone reorders the URL map, the logging tests keep passing while meaning
something completely different.

**A test that pins the assumption underneath your other tests is worth more than
another test of the feature.** They're rarer than they should be, because nobody
writes a test for the thing that isn't changing.

## Where this series lands

Six parts, and the failures have a shape in common that I didn't see until I wrote
them out.

The gate that validated its own input. The rejected deploy that kept running. The
credential with a thirty-day fuse. The edge with no logs. Not one of them would
have paged anyone. Every one of them was the system quietly *not* doing something,
with no signal that would ever have said so.

That's the real argument for building it dark, and it's a better one than "safer
cutover." The dark period isn't waiting time. It's the only window you get where
the system is real enough to be wrong and cheap enough to be wrong in — where you
can find the failures that don't announce themselves, before they're carrying
everybody's traffic.

The cutover itself is a DNS record. The value was in the month before it.

Which is, I notice, the same sentence I wrote at the start of the baseline series
about the two months before *that*. I set out to write about a migration and
ended up writing thirteen posts about instrumentation — about the difference
between a system that is working and one that is merely quiet, and how little of
that difference is visible unless you build something that can tell you.

If there's one thing to take from either series: the failures that hurt aren't
the ones that page you. Go and find the checks you've never seen fail.
