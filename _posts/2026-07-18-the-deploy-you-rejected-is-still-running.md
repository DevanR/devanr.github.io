---
layout: post
title: "The Deploy You Rejected Is Still Running"
excerpt: "A candidate revision failed its smoke test and never took traffic. It also never stopped — and it spent a day running scheduled jobs against the production database."
categories: articles
tags: [cloud-run, release-engineering, blue-green, incidents, ci-cd]
comments: false
share: true
modified:
series: "Building it dark"
series_part: 4
---

The safe-rollout gate did its job. A new revision came up at zero traffic under a
private tag, the smoke test failed, and the deploy refused to promote it. The
production service kept serving the previous revision. The pipeline went red.
Textbook.

Nobody asked what happened to the revision we'd just rejected.

## What happened to it

It kept running. For a day. Executing scheduled work against the production
database.

The mechanism is three innocuous facts standing on each other's shoulders:

1. A revision that carries a **tag** must keep serving its own private URL, so
   the platform considers it *addressable*.
2. The platform will not deactivate an addressable revision. Ever. That's the
   contract — the tagged URL is supposed to work.
3. These services run with a **minimum instance count of one**, so "not
   deactivated" means a container is up. Continuously.

And that container runs the application's scheduler, which is in-process: timers
that start when the process starts, pointed at the production database and a
third-party CRM. It has no idea it lost a smoke test. Nothing told it. Nothing
could — it's just a process that booted.

The coordination lock the application uses for scheduled work lives in a
per-instance sidecar, so it could not arbitrate between the rejected revision and
the one actually serving traffic. It was never designed to. Two processes, same
timers, same production data, in parallel.

## The evidence

I want to be precise about how this was established, because "the tag was the
cause" is exactly the kind of claim that's easy to assert and hard to prove.

It was a controlled comparison, not an inference. Four revisions of the same
production service, all with the same minimum-instance setting:

| Revision | Traffic | Tag | Active |
| --- | --- | --- | --- |
| the serving revision | 100% | — | yes |
| the failed candidate | 0% | `candidate` | **yes** |
| an older revision | 0% | — | no |
| an older revision | 0% | — | no |

Three revisions at zero traffic. Two inactive. One very much alive. The only
difference between them is the tag.

That table is the whole argument, and it took about four minutes to produce. It's
worth the habit: when you think you understand a platform behaviour, find the case
that differs in exactly one variable before you write the fix.

## The fix

Drop the tag when a rollout is not promoted. The revision stops being addressable,
the platform deactivates it, the container goes away.

The interesting work was in the edges rather than the mechanism:

- **Every non-promotion path**, not just the obvious one. A failed health check, a
  failed real-time smoke, an unresolvable candidate URL, an apply that fell over
  *after* its traffic write landed, and a cancelled job. "Cancelled" is the one
  people miss — someone hits stop, and the residue is identical.
- **Never after a successful promotion**, where promotion collapses the tag
  itself, and never for a service deploying without a tag at all.
- **Idempotent and fail-soft.** Cleanup must not mask the smoke failure that got
  us here. The job still ends red; that is the signal that matters.
- **A loud, actionable failure.** If cleanup itself fails, the run emits the exact
  copy-pasteable command and says plainly that the revision is still running
  scheduled work. Not "cleanup failed" — the consequence, in words, so the person
  reading at 11pm doesn't have to reconstruct this post.

Plus the one-off: an existing ghost revision that had been running for a day. Not
something a merge can fix — an operator action, with the command written into the
rollback documentation so the next person doesn't have to derive it.

## The lesson, which I have now learned twice

**"Not receiving traffic" is not "not running."**

I had internalised the traffic split as the safety boundary. Zero percent means
harmless. It doesn't. Zero percent means no *inbound requests* — and an inbound
request is only one of the ways a process does work. Timers, queue consumers,
change streams, cache warmers, replication clients: all of those start when the
container starts and run regardless of what the routing layer thinks.

The second time I learned it was two weeks earlier, in the same phase, from the
opposite direction: the entire dark stack — a full parallel copy of production
serving no customers — also had to have its scheduler explicitly disabled, for
precisely the same reason. Same insight, different corner of the system, and I
didn't connect them until I'd been bitten by both.

There's a design point underneath. A rollout gate is a state machine, and
**rejection is a state, not the absence of one.** We design the happy path
carefully — deploy, verify, promote — and treat failure as the thing that didn't
happen. But failure isn't an absence. It leaves residue: half-created resources,
warm containers, tags, locks, partial writes. Residue with a scheduler in it is an
outage sitting quietly in the diary, waiting for a slow week.

So when you build the gate, write down what the rejected branch *leaves behind*,
in the same sitting. Not later. Later is a day of duplicate cron runs against
production and a table you have to build to prove why.

What does your failed deploy leave behind?
