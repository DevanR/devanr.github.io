---
layout: post
title: "Build It Dark"
excerpt: "How to migrate a live product onto a new stack without a cutover weekend: build the whole new production alongside the old one, serving nobody, until the only remaining step is a DNS change."
categories: articles
tags: [cloud-run, gcp, infrastructure, opentofu, release-engineering, migration]
comments: false
share: true
modified:
series: "Building it dark"
series_part: 1
---

A client's product ran on two long-lived virtual machines. One served the web
app, one served the API, both had been up for years, and both were the sort of
box where nobody was entirely sure what was installed on them. We were moving
the whole thing onto a managed container platform.

The two months before this went into the quality baseline — characterisation
tests, gates that could actually fail, configuration that stopped being baked into
the build. That was the *Earning the right to move* series. This is what it was
for.

The interesting question was never "can we build the new stack." It was "how do
we get onto it without a cutover weekend."

So we set one rule up front, and it has shaped every decision since:
**everything net-new is additive and dark.** Nothing new serves a real user until
a DNS record moves.

## What "dark" actually means

Both environments — staging and production — are now stood up on the new
platform. Two services each, behind a same-origin HTTPS load balancer, with
managed certificates, a WAF policy, secrets, dedicated runtime identities, and a
deploy pipeline that gates every promotion behind a smoke test.

All of it reachable. None of it serving a customer.

Each environment got a second hostname — a parallel address that only the team
knew. The live hostnames kept pointing at the old VMs, which we did not touch at
all. Not one config change, not one restart.

The property that buys you is a rollback with no drama. If the new edge is wrong,
you delete a DNS record. If it's badly wrong, you destroy the entire
infrastructure root — it's an independently-applied unit with its own state, and
nothing live depends on it. There is no "restore the old config" step, because
the old config was never modified.

That is worth restating, because it's the whole trick: **the safest migration is
one where the old system never learns that a migration is happening.**

## Dark is not a sandbox

Here's the part that catches people, and it caught us enough that we put it in
the docs in bold.

The parallel production stack reads and writes the *real production database*.

That's deliberate. The entire point of a dark stack is to validate against real
data, real volumes, real edge cases in your records — not against a seeded fixture
that agrees with your assumptions. But it means a hostname nobody has heard of,
with no traffic and no monitoring dashboard on the wall, is production.

We verified it rather than assumed it. A probe against the parallel production
host found a production-only user account and not the staging one; the parallel
staging host was the exact inverse. Both results written down, with the date.
Then a warning in the developer docs: treat anything you do on that host as done
to production, because it is. Use staging for anything destructive.

The failure mode we were heading off is obvious in hindsight and invisible in the
moment — an engineer treating an unfamiliar hostname as a scratch environment
because it feels like one.

## Dark also means the background work has to be off

This one I did not see coming.

The API service runs its scheduler *in-process*: a handful of timers started when
the process boots. There is no separate cron service. That's fine when exactly one
copy of the application is running.

Stand up a dark production copy with a minimum instance count of one, and you now
have two processes running the same scheduled work against the same production
database and the same third-party CRM. Nobody is using the dark stack. Its
scheduler doesn't care.

Worse, the application's own coordination lock lives in a per-instance sidecar,
so it cannot arbitrate between the two stacks at all. The lock was never designed
to.

So the dark services ship with the scheduler explicitly disabled — and disabled
via a deliberately guarded variable, with a comment explaining exactly what turning
it on means, rather than a free tunable somebody flips while debugging.

The general shape: **a dark copy of a service is only dark on the paths that
require a request.** Anything the process does on its own initiative — timers,
queue consumers, change streams, warmers — is live the moment the container
starts. Enumerate those before you stand up the second copy, not after.

## Who is allowed to apply it

One more deliberate slowdown. The edge is not deployed by CI.

The deploy identity in this system is scoped tightly: it can update container
services and nothing else. Load balancers, networks, certificates and WAF policies
are outside its role on purpose, so a compromised or careless pipeline cannot
repoint traffic. The edge is applied by a human, by hand, following an ordered
runbook that lives next to the code.

That is slower, and it is the correct trade. Application deploys happen many
times a day and should be automated to the point of boredom. Edge changes happen
a handful of times a quarter, and each one can take the whole product offline.
Those two things do not want the same permissions or the same ceremony.

## What it costs

Being honest about the bill:

- **You pay for two productions** for the duration. Real money, for weeks.
- **You maintain two systems.** Every application change during the migration has
  to keep working on the old VMs *and* the new stack.
- **Nothing forces the last step.** A dark stack can sit there indefinitely,
  quietly accruing cost, because the thing that would create urgency — pain — is
  exactly what you engineered away. That risk is real and it is managerial, not
  technical.

What you buy is a cutover that is a DNS change, reversible in minutes, rehearsed
against real data, with the old system still warm behind it.

I'll take that trade every time. But name the cost out loud when you propose it,
because "build a second production and run it for a month" sounds extravagant
right up until you compare it to a Saturday-night migration with a rollback plan
nobody has ever executed.

## The strange definition of progress

So here is where it sits today: both environments fully served through the new
stack, on hostnames no customer uses, with the live traffic still running on the
machines we set out to replace.

That reads like a project that hasn't got anywhere. In one narrow sense it
hasn't — no DNS record has moved, and a sceptic would say nothing has actually
migrated. But the remaining risk is now one DNS record per environment, and every
other unknown is being resolved in daylight, on real data, with the old system
untouched behind it.

The interesting part is what that daylight keeps turning up. A deploy gate that
was validating its own input. A rejected deploy that never stopped running. A
credential quietly counting down to an expiry. An edge nobody could see. None of
those would have been visible before a cutover, and every one of them has been
cheap to fix precisely because nothing is cut over yet.

They're the next five parts of this series.

Which is the argument for building it dark, better than anything I could say about
it in the abstract.
