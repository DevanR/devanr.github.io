---
layout: post
title: "Earning the Right to Move"
excerpt: "Two months of test and CI work on an inherited codebase before a single line of infrastructure changed. Not diligence for its own sake — you cannot safely move a system you cannot describe."
categories: articles
tags: [legacy-code, testing, ci-cd, engineering-management, migration]
comments: false
share: true
modified:
series: "Earning the right to move"
series_part: 1
---

A client's product is moving onto a new platform. New runtime, new deploy
pipeline, new networking — the whole stack underneath an application that has been
running for years.

We haven't touched any of it yet. For about two months, across three repositories
with years of history, almost nothing has shipped that a user could see. What
shipped instead was formatting, pre-commit hooks, coverage instrumentation,
characterisation tests, a type-check job, and a set of security scans that were
made capable of failing.

That is a hard thing to put on a status report. I think it's also the only thing
that will make the migration boring, and this series is the argument for why —
plus everything I got wrong along the way.

## The argument

You cannot safely move a system you cannot describe.

A runtime migration — new platform, new deploy pipeline, new networking — changes
everything about *how* the code runs and nothing about *what* it does. Which
sounds like a clean separation, until something breaks and you have to answer:
did we change the behaviour, or did we just move it?

Without a baseline, that question has no answer. You get a debate. Someone says
the notification emails look different, someone else says they always looked like
that, and there is no artefact in the repository that settles it. That debate,
repeated weekly, is what makes migrations drag on for quarters.

With a baseline, it's a diff.

So the sequencing wasn't diligence for its own sake. Each thing existed to make a
specific later question answerable:

- **Formatting and pre-commit hooks** — so that a later diff shows behaviour
  changes and not whitespace. Cheap, and it comes first because everything after
  it is read as a diff.
- **Coverage instrumentation, then a ratchet** — so the test suite can only get
  better, without anyone running a test sprint.
- **Characterisation tests over the handlers due to move** — so "did the behaviour
  change?" is a test result rather than an argument.
- **A blocking type-check** — so a refactor's collateral damage surfaces in CI
  rather than in production.
- **Security scans that actually fail** — because the migration touches every
  dependency, image and identity in the system.
- **End-to-end tests on real devices** — because the parts most likely to break in
  a platform move are the parts that cross a boundary.

Only then: infrastructure.

## What it costs, said plainly

The client paid for roughly two months of engineering with no feature output.

I want to be honest about that rather than dress it up, because "invest in
quality" is the easiest thing in the world to say and the hardest to sell. The
sell isn't "quality is good." The sell is specific:

> Every week of this makes the migration's unknowns smaller. The alternative isn't
> a faster migration — it's the same migration with the risk moved to production
> and the discovery moved to your customers.

That framing worked because it's true and because it's falsifiable. If the
baseline work hadn't made later changes cheaper and more confident, you'd see it.

## The trap: advisory forever

The failure mode of this whole approach isn't that the work doesn't happen. It's
that it happens and never gets teeth.

Every one of these tools has a comfortable mode where it reports but does not
block. Coverage that prints a number. A scanner that posts a comment. A type-check
somebody runs locally. Teams adopt the tool, tick the box, and the tool never
changes anyone's behaviour because nothing depends on it.

Our coverage ratchet shipped in exactly that state — advisory — and sat there for
weeks without flipping. That's the default outcome, not the exception. Part four
of this series is about what it actually took to flip it, and the answer wasn't
willpower.

## What's coming

Seven parts, each a thing I got wrong or learned the hard way:

1. This one — the sequencing and the argument for it.
2. **Frozen** — characterisation tests as receipts rather than judgements, and
   the tagging convention that tells a future refactor what's load-bearing.
3. **A script CI doesn't run is a suggestion** — nine type errors hiding in the
   one place nobody type-checks, and why a "blocking" job can block nothing.
4. **Advisory forever** — how a gate actually gets teeth.
5. **Fail closed, or don't bother** — two security scanners that were
   structurally incapable of reporting a problem.
6. **The flaky test was telling the truth** — two real defects wearing a flake's
   clothing.
7. **Build once, run anywhere** — the unglamorous changes that had to land before
   the migration could start at all.

The through-line, if you want it up front: **almost every problem in this series
was something that looked fine.** A passing check, a green scan, an intermittent
test everyone re-ran. The baseline work wasn't about finding bugs. It was about
building the instruments that could tell the difference between working and
merely quiet.

Which is, I suspect, going to be excellent preparation for the migration itself.
That gets its own series when it's done.
