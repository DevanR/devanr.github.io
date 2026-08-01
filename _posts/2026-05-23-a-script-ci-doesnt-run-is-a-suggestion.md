---
layout: post
title: "A Script CI Doesn't Run Is a Suggestion"
excerpt: "The type-check command existed. Nothing ran it. Nine errors had accumulated in the one directory nobody type-checks — and a 'blocking' CI job can still block precisely nothing."
categories: articles
tags: [ci-cd, typescript, testing, legacy-code, engineering-practice]
comments: false
share: true
modified:
series: "Earning the right to move"
series_part: 3
---

The repository had a type-check script. It had had one for a long time.

Nothing ran it. Not CI, not the pre-commit hook, not the build. It sat in the
package manifest looking like a quality control, and it was a suggestion.

When I finally wired it into CI, nine errors came out. Every one of them in
`tests/`.

## Why the test directory is where the errors go

This is the part worth internalising, because the mechanism generalises well
beyond one language.

Three things were true at once:

1. **The test runner transpiles rather than type-checks.** Modern runners strip
   types with a fast bundler and execute. Types aren't validated — they're
   deleted. A test file can be riddled with type errors and pass every run.
2. **The production build only looked at a subset of the source.** Its config
   scoped the emit narrowly. Anything outside that scope was never seen by the
   compiler at all.
3. **Nobody runs the type-check by hand on test files.** You run it, if ever,
   because you're touching source.

So `tests/` sat in a blind spot formed by the intersection of three tools that
each assumed one of the others was covering it. Errors accumulated there for
months, invisible, and would have stayed invisible indefinitely.

Look for that shape in your own repo. **Wherever two tools' coverage areas don't
quite meet, drift accumulates in the gap** — and the gap is usually in test code,
build scripts, or infrastructure config, because those are the places people
think of as "not really the codebase."

## The casts were the tell

The interesting thing about the nine errors is that none of them were sloppiness.
They were all *drift* — code that was correct when written and had quietly stopped
being correct.

The clearest example: several tests cast the result of a database query to an
expected shape. That cast compiled fine originally. Then the query builder's
return type changed to a union — array, single document, or null — that no longer
overlapped the target shape, and the cast became a lie the compiler would have
rejected if anyone had asked it.

The fix was to stop casting and pass the concrete shape as a generic instead.
Identical at runtime; the difference is that a generic asks the compiler a question
while a cast tells it to be quiet.

That's the general lesson about type assertions in test code. **A cast is a place
you told the compiler to stop looking.** Fine at the time. But it doesn't decay
gracefully — it silently absorbs every subsequent change to the thing it was
covering for, and you find out when someone finally turns the lights on.

Everything I changed was type-level. No runtime code was touched, no test
behaviour altered. That mattered for reviewability: a nine-error cleanup that also
edits application code is a pull request nobody can sign off on with confidence.

## The part that nearly didn't count

Here's the bit I'd most want to pass on.

Adding a blocking CI job does not, by itself, block anything.

The job ran. It was not `continue-on-error`. It went red on a type error. And a
pull request with that red job was still perfectly mergeable — because branch
protection didn't list it as a **required status check**.

A CI job is a thing that produces a result. A gate is a thing that stops a merge.
Turning the first into the second is a repository settings change, usually
admin-only, and completely separate from the code. So it lands in a pull request
as an unticked box — "add to branch protection: out of band" — and then it lands
in nobody's week, and you have a CI job producing a red cross that everyone learns
to scroll past.

That is exactly how a quality initiative dies: not rejected, just never made
required.

There's a second-order version of this that bit us later. When the security scans
were eventually made required, they had a path filter on them — only run when
relevant files change. A required check that a filter can skip never reports at
all, and the pull request sits forever at *"Expected — waiting for status,"*
unmergeable. So the filters had to come off first. **A required check must always
report, including when it has nothing to do.**

The sequence that actually works, in order:

1. Add the job.
2. Get it green on the default branch.
3. *Then* make it required — and confirm the required-check name matches the live
   check-run name, which for matrixed jobs is not the bare job name.
4. Verify a deliberately failing pull request is genuinely unmergeable.

Step four is the one everyone skips, and it's the only one that proves the other
three worked.

Have you ever confirmed your required checks actually block a merge — or is it
assumed?
