---
layout: post
title: "Build Once, Run Anywhere"
excerpt: "Twelve config values inlined at build time made every image environment-specific — which quietly makes 'promote the exact artefact you tested' impossible. The unglamorous changes that had to land before a migration could start."
categories: articles
tags: [twelve-factor, release-engineering, ci-cd, configuration, migration]
comments: false
share: true
modified:
series: "Earning the right to move"
series_part: 7
---

The last stretch of baseline work was the least interesting to describe and the
most load-bearing: a handful of changes that had to exist before the migration
could start at all.

The clearest one was configuration.

## The build was baking the environment in

The web app read twelve public configuration values — API URLs, upload targets,
authentication client settings — through the build tool's compile-time
environment. Which means the bundler *inlines* them. They stop being
configuration the moment the build finishes; they're constants in the artefact.

That is completely fine right up until you want a deploy pipeline that builds once
and promotes the same artefact through environments.

And you do want that. It's the single property that makes a promotion meaningful:
the thing running in production is byte-identical to the thing that passed in
staging. Rebuild per environment and you've thrown that away — you're now
promoting a *recipe*, and hoping it produces the same result twice, on a different
day, with a fresh dependency resolution.

With build-time inlining, the pipeline I wanted was not merely awkward. It was
impossible. A promotion would have meant a rebuild, and a rebuild is a new
artefact.

So the values moved to runtime resolution — read from the process environment when
the server starts, rather than substituted when the bundle is built. The app runs
on a Node adapter, so this was available; it just hadn't been used.

The test that proves it is the one I'd insist on: **a clean production build with
none of the configuration set at all.** If the build succeeds with an empty
environment, nothing is baked in. That's a far better assertion than any test of
what the values resolve to.

## Fail loud at boot, not quietly per request

The obvious way to do runtime config is to read the variable where you need it.
Then a missing value gives you `undefined` interpolated into a URL, and a request
that fails at 3am with a stack trace pointing at a fetch call.

Instead: one module resolves every value once, and a server startup hook validates
the required ones. On a deployed artefact, a missing required key **throws at
boot** — the server refuses to start. Locally and in tests it warns.

This is the same instinct as failing closed in a security gate, applied to
configuration. A misconfigured service that starts is worse than one that doesn't,
because it will serve wrong behaviour for hours before anyone connects the
symptoms to a deploy. A service that refuses to boot tells you within seconds,
with the key name.

Two details worth stealing:

**Empty string normalises to undefined.** Otherwise validation and consumption
disagree — the key is "present" so validation passes, and then something
interpolates an empty string into a URL. Same class of bug, one layer along.

**Detect "am I a deployed artefact" from a build-time flag, not the environment
name.** The obvious check is whether the environment variable says production. But
that variable isn't guaranteed to be set on a container platform, so the check
silently degrades to the lenient branch in exactly the place you wanted it strict.
A flag baked in by the build tool is a reliable "this is a built artefact" signal
because nothing at runtime can be missing it.

That's a general trap: **any strictness that keys off an environment variable can
be disabled by that variable being absent.** If the strict mode matters, key it off
something that cannot go missing.

## The other two

Two smaller changes landed in the same stretch, both of which looked pointless at
the time.

**A health endpoint in each service.** Nothing needed one yet. Weeks later, the
container platform's readiness probe and the deploy pipeline's smoke test both
depended on it entirely — and, as it turned out, the deploy gate's correctness
depended on exactly what it reported. Adding it early meant the migration never
had to introduce a new endpoint and a new deploy mechanism in the same change.

**Pinning the runtime version.** One file naming the version, the package manifest
declaring the range, and CI deriving its version from that file rather than
hardcoding it. Trivial. It means the container base image, the CI runner and every
developer's machine are provably the same major version — so "works locally,
fails in the container" stops being on the list of things a migration failure
could be.

Both are examples of the same move: **reduce the number of variables that change
at once.** A migration is a large change to the environment. Every unrelated
difference you can eliminate beforehand is a hypothesis you don't have to test
during a cutover.

## What the baseline was for

That's the end of the baseline, and the migration starts.

Runtime config is what makes build-once-promote-the-digest possible, which is the
model the deploy pipeline gets built around. The health endpoints become the smoke
test the deploy gate depends on — and, as it turns out, the place I'd later find
the most embarrassing bug of the whole project. The frozen tests are how we'll
know the behaviour hasn't shifted. The gates are what make every infrastructure
pull request produce a real signal.

None of it was visible to a user. All of it was load-bearing.

The one-line version, if you want it: **the work that makes a migration boring
happens before the migration, and it mostly consists of building instruments that
can tell the difference between working and merely quiet.**

What happened next has its own series.

If you're staring down a platform move: what in your build is environment-specific
right now, and could you promote an artefact from staging to production without
rebuilding it?
