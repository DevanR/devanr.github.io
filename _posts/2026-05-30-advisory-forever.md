---
layout: post
title: "Advisory Forever"
excerpt: "Every quality gate ships in advisory mode and most of them stay there. Flipping ours to blocking took two specific things, and neither of them was willpower."
categories: articles
tags: [ci-cd, engineering-management, code-coverage, engineering-practice]
comments: false
share: true
modified:
series: "Earning the right to move"
series_part: 4
---

We shipped a per-file coverage ratchet. It ran on every pull request. It computed
a proper delta table. It was advisory.

Weeks later it was still advisory, and it had never changed a single decision
anyone made.

That is the normal outcome. "We'll ship it advisory first and flip it once the
team's comfortable" is one of the most reliably broken promises in engineering,
somewhere just behind "we'll dedicate a sprint to tests." The tool gets adopted,
the box gets ticked, and nothing downstream of it ever changes.

I've now watched this happen enough times to think the failure is structural
rather than a matter of discipline. Two things fix it.

## One: it was invisible, not just non-blocking

The ratchet wrote its delta table to the CI run's step summary.

Nobody opens the step summary. You open a pull request, you see a list of green
ticks, you merge. To find the coverage delta you had to click into the Actions
run, find the job, and scroll — a deliberate act of curiosity on a check that had
already told you, by being green, that you didn't need to.

So the first change wasn't about enforcement at all. It was moving the signal to
a **sticky pull-request comment**: total delta as a headline, per-file table
underneath, upserted in place on every push so it never becomes a thread of stale
comments.

Suddenly the number was in everyone's face on every pull request, for weeks,
while still blocking nothing.

That's what made the eventual flip uncontroversial. By the time it had teeth,
every person on the team had already watched their own number move dozens of
times. Nobody was surprised by it, nobody had to be convinced it was accurate, and
nobody discovered the tool and its enforcement on the same day.

**Advisory mode is only useful if the advice is unavoidable.** An advisory signal
nobody sees isn't a gentler gate — it's a gate that doesn't exist, plus
maintenance.

## Two: the flip was built in from the start

The second change was smaller and did just as much work: an environment flag that
switches the ratchet from reporting to gating.

With the flag in place, "make coverage blocking" stops being a project. It's a
one-line change to a workflow file, reviewable in ten seconds, revertible in ten
more. Nobody has to schedule it, scope it, or defend it in planning.

Compare that to the alternative, where flipping means someone re-opens the script,
works out where the exit codes go, discovers three edge cases, and now owns a
week. That work never gets prioritised against a feature, which is why the flip
never happens.

**If you ship a gate in advisory mode, ship the switch at the same time.** Then
put a date on it. An advisory gate without a scheduled flip date is a permanent
advisory gate, and you should be honest with yourself that you've built a
dashboard.

## The rule that makes advisory mode actually advisory

One detail I'd insist on anywhere: in advisory mode, **every** exit path returns
success. Not just the "coverage went down" path — the internal errors too, and the
failure to post the comment.

The comment post is wrapped so that a permissions problem or an API blip logs a
warning and moves on. That looks like sloppiness. It isn't. If your advisory
signal can turn a pull request red for reasons unrelated to what it's advising,
people stop trusting the job, and the distrust doesn't stay neatly contained to
the advisory part — it spreads to the whole check.

An advisory tool has exactly one job: be right, be visible, and never be the
reason someone can't ship. Break that once and you've spent the credibility you
needed for the flip.

## What flipping actually looked like

Two changes, weeks apart, in a deliberate order.

First the ratchet went to enforce mode — one flag, one line, on a signal everyone
had been watching. Then the same policy was applied uniformly across all three
repositories, along with the other gates: type-check confirmed blocking, the
container scanner made blocking on high-and-critical findings, and the whole
policy written into a short document committed identically in each repo, so
"what are the gates here" has one answer rather than three.

And the sequencing rule I'd keep: **verify green, then require.** The tightened
configuration merges first and proves itself on real pull requests; only after
that does anyone register it in branch protection. Doing it the other way round
means your first evidence that the gate is too tight arrives as a blocked
release.

## The pattern, generalised

Any check you introduce moves along the same path:

1. **It exists** — someone can run it.
2. **It runs** — CI runs it on every change.
3. **It's seen** — the result appears where decisions are made, not in a log.
4. **It blocks** — a failure stops a merge.
5. **It's required** — branch protection knows about it.

Most quality initiatives get to step two and stop, which feels like progress and
delivers none. Steps three and five are the ones that get skipped, and they're the
two that don't involve writing any interesting code — which I don't think is a
coincidence.

Where does your last-introduced quality check sit on that list, honestly?

---

*A companion piece on the ratchet mechanism itself — why per-file rather than a
global percentage, and why a floor beats a target — is in the backlog.*
