---
layout: post
title: "Frozen: Tests as Receipts, Not Judgements"
excerpt: "Characterisation tests don't assert that behaviour is correct. They assert that it hasn't changed. Conflating those two is why people believe legacy code can't be tested."
categories: articles
tags: [legacy-code, testing, characterisation-tests, refactoring, migration]
comments: false
share: true
modified:
series: "Earning the right to move"
series_part: 2
---

The objection to writing tests for inherited code is always some version of the
same thing: *we don't know what the correct behaviour is.*

It's a fair objection. Nobody who wrote the original code is still on the team.
The requirements live in a chat archive. Half the edge cases are load-bearing
accidents that a customer now depends on.

And it's the wrong objection, because it assumes a test has to encode a judgement.

## Two different tools with the same syntax

A unit test says: *this is what the code should do.* It encodes an intention. If
it fails, the code is wrong.

A characterisation test says: *this is what the code does today.* It encodes an
observation. If it fails, something **changed** — and you now have to decide
whether you meant it.

Same test framework, same assertion library, completely different tool. The second
one requires no knowledge of correctness at all. You do not need to know why the
notification email includes a particular field. You need to know that it does, so
that when it stops, you find out in CI rather than from a customer.

That reframe is the whole unlock. You cannot write a correctness test for code you
don't understand. You can always write a receipt.

## What we froze

The plan was to move the runtime and, later, replace the chat backend entirely. So
the receipts went where a change would be most expensive and least visible:

- **The real-time message contract** — send, get, get-after, edit, delete, react,
  and a two-client fan-out test proving a message published by one connected
  client arrives at the other. That last one can't be faked with a single socket.
- **The outbound email and its calendar attachment**, snapshotted whole.
- **The submit-flow contract**, end to end.
- **The three-hourly notification poller**, which is the interesting one.

That last suite drives the module exactly as production does: start it, advance
fake timers by three hours, let one cycle run to completion including its
reschedule, then stop. The snapshot captures the entire contract in one object —
the database query filter, its projection, the full selection pipeline, the exact
ordered webhook bodies, and which records get stamped as notified. Plus both edges
of the concurrency lock: acquired on a normal cycle, and the short-circuit when
it's already held, asserting that nothing else runs.

That's a scheduled job that fires eight times a day against production data and
had, until then, no executable description of what it did.

## The bit I'd steal: tag them

Here's the problem with a pile of characterisation tests. Six months later,
someone refactors the module and half the suite goes red. How do they know whether
they've broken a contract or merely broken some scaffolding a previous developer
wrote to explore the code?

They don't. So they delete the ones that look annoying.

So the tests due to outlive the migration got tagged. A tiny wrapper —
`frozen(name, fn)` — marks a suite as a **migration anchor**: load-bearing,
deliberately frozen, do not casually delete. Everything else is ordinary.

Two implementation details that took longer to get right than the idea:

**It's a tag, not a name prefix.** The obvious implementation is renaming the
suite to `[frozen] whatever`. Don't. The snapshots are keyed by the top-level
suite name, so renaming churns every single committed snapshot file — turning a
zero-risk labelling change into a diff nobody can review. A first-class test tag
leaves every snapshot key byte-identical.

**The reporter walks to the outermost tagged ancestor.** Tags inherit downward, so
after tagging a parent, every nested block carries the tag too. Grouping by the
*nearest* tagged suite splits one frozen suite into phantom sub-groups; grouping
by the outermost suite name mislabels a frozen anchor that happens to sit under an
untagged parent. Neither is obvious until you look at the output and it's subtly
wrong.

The payoff is a boxed section in the existing test run: **frozen migration-anchor
tests**, with a pass/fail/skip count and the list of suites. No extra test
execution — it's a second reporter alongside the default one. And a filter to run
only the anchors locally, which is what you want during a refactor.

## What I deliberately didn't build

There is no CI guard that fails when the frozen count drops.

I thought about it and left it out. The tag's job at that point was to make the
anchors *visible* — so that a developer deleting one has to notice they're
deleting one. Enforcement is a different decision, with different politics, and
bundling it into the labelling change would have made the labelling change
contentious.

That's the same sequencing mistake I'd made elsewhere and eventually learned to
run deliberately: **visibility first, enforcement second, and never in the same
pull request.** More on that in part four.

## The generalisation

Legacy code isn't untestable. It's un-*judgeable*, which is a different problem
with a different answer.

Stop trying to write the test that says what the code should do. Write the one
that says what it does, snapshot it wholesale, and tag it so the next person knows
it's load-bearing. You get a change-detector for a system nobody fully
understands, which is precisely the instrument a migration needs.

The tests aren't a verdict. They're a receipt. And you can write a receipt for
something you don't understand at all — that's rather the point of receipts.

What's the oldest scheduled job in your system, and is there anything in the repo
that describes what it does?
