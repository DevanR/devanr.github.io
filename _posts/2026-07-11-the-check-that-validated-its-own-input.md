---
layout: post
title: "The Check That Validated Its Own Input"
excerpt: "A deploy gate asserted that the running build matched the commit being deployed. It passed every time, including the times it was wrong, because both sides of the comparison came from the same variable."
categories: articles
tags: [release-engineering, ci-cd, testing, supply-chain, cloud-run]
comments: false
share: true
modified:
series: "Building it dark"
series_part: 3
---

The deploy gate looked airtight when I described it to people.

A new revision comes up at zero traffic under a private tag. A smoke test hits
its health endpoint and asserts two things: the service reports healthy, **and**
the version it reports matches the commit we asked to deploy. Only then does a
second apply shift traffic to it.

That second assertion is the good bit. It doesn't just prove something is
running, it proves the *right build* is running. Or so I told people.

It proved nothing at all.

## The shape of the bug

Trace the value. The commit SHA enters the deploy workflow once, and then goes to
two places:

- It is passed into the container as an environment variable, which the health
  endpoint reads and reports as its `version`.
- It is passed to the smoke test as the *expected* value.

One variable, stamped into the thing being measured and used as the yardstick.
The comparison can only fail if the wiring between those two lines is broken.

It is a tautology wearing a hard hat.

## The fallback that made it harmful

On its own, a tautological check is merely useless. This one was worse, because
of a default.

The workflow resolved the commit as: the dispatched input, **or** the payload
value, **or** the CI runner's own commit. That last fallback is the infrastructure
repository's `HEAD` — a commit that has nothing to do with the application build
at all.

The automated path always supplied a real value, so this never bit. The manual
path declared the input optional.

Then two production deploys went out by hand, dispatched the minute an
infrastructure PR merged. Both application containers were stamped with the
*infrastructure repository's merge commit* — a SHA that exists in neither
application repository. From the run log:

```
smoke: healthy; version matches dispatched sha <the infra repo’s merge commit>
```

Green. Both times. Every health probe on production was reporting an
infrastructure commit as the application version, and the check that exists to
catch exactly that reported success.

Nothing was broken, to be clear. The right images were deployed. But for the
better part of a day, the system's own answer to "what is running?" was a
confident lie, and the gate designed to detect confident lies had signed it off.

## The fix, in three parts

**Make the input required, with no fallback.** The commit is now mandatory, and
the deploy fails closed on a missing value, a malformed one, or one that belongs
to the infrastructure repository rather than an application. The dispatch path
that carries no input schema gets the same check at runtime, because a validation
that only exists in the form definition isn't a validation.

**Give the comparison an independent second source.** The commit is now verified
against the container image's build provenance *before* anything is planned. That
value is produced by the build system, signed, and not restatable by the deploy
workflow. A plausible-looking wrong SHA now fails the deploy outright, rather than
mislabelling the build.

**Correct the documentation that oversold it.** Two places described the assertion
as a stale-image guard. It never was one, and leaving that written down is how the
next person builds on a guarantee that doesn't exist.

There's a fourth part still open, and I'd rather say so than pretend the story
ends neatly: the version really wants to be *read out of the image* at build time,
which needs a change in the application repositories' build. Until that lands, the
only fully honest answer to "what build is serving?" is the image digest on the
serving revision — the one value nothing in the pipeline can restate. That went in
the developer docs, with the health endpoint explicitly labelled as *not* build
evidence.

## The generalisable bit

I've since started asking one question of every assertion I write:

> **What would have to be broken for this to fail?**

If the honest answer is "the wire between these two lines of my own code," it is
not a gate. It is a self-consistency check, and self-consistency is the one
property a broken system retains most reliably.

A check is worth exactly as much as the *independence* of the two things it
compares. Same variable, no value. Same process, little value. Same team's
assumptions, some value. A signed artefact from a system that has no idea your
check exists — that's a gate.

This pattern is everywhere once you look for it. Tests that assert a function
returns what a fixture built from the same function says it should. Monitoring
that reads the deployment manifest to decide what version *should* be running.
Contract tests generated from the implementation. Every one of them will hold
green through the exact failure it was written to catch.

The tell is comfort. A check that has never once failed, in a system that has
definitely had problems, is not a check that's protecting you. It's a check that
isn't looking.

What's the most tautological green check you've found in your own pipeline?
