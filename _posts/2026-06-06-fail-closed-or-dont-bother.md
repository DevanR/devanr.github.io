---
layout: post
title: "Fail Closed, or Don't Bother"
excerpt: "Two security scanners ran on every pull request and neither could reliably report a problem. Every gap failed the same direction: the safe-looking default was 'pass'."
categories: articles
tags: [security, ci-cd, sast, supply-chain, engineering-practice]
comments: false
share: true
modified:
series: "Earning the right to move"
series_part: 5
---

The repositories had security scanning. A container/dependency scanner and a
static analysis scanner, both running on pull requests, both posting comments,
both green.

Neither was structurally capable of telling us we had a problem.

Not because they were badly configured in any way that looks wrong. Because at
every point where something could go slightly sideways, the code took the
comfortable branch — and the comfortable branch, every single time, was *pass*.

## Four ways a scanner reports "clean" without scanning

**A partial scan that exits zero.** The dependency scanner writes results to a
file, and the gate reads that file. If the scan half-completed, the file can exist
and parse fine while containing no results array at all. Zero findings. Green
tick. The gate now reports `Errored` when the results are missing, unparseable,
structurally absent, or the scan step itself failed — never a silent pass.

**A diff too large to inspect.** The static analyser distinguishes new findings
from pre-existing ones by matching them against the lines your pull request
changed. To do that it needs the patch for each file. On large diffs the API
*omits* the patch — and it caps the file list entirely. So on a big pull request,
a genuinely new finding could be matched against an incomplete picture of what
changed and classified as pre-existing. Silently downgraded, on exactly the pull
requests you most want scrutinised.

Fixed by failing closed in both directions: a file with no patch is treated as
entirely changed, and a truncated file list means the whole diff is treated as
changed. Noisier on huge pull requests, which is the correct trade — a large
change should be *harder* to sneak something through, not easier.

**A filename with a space in it.** The analyser's output encodes file paths as
URIs, so a space becomes `%20`. The comparison used the raw path. A finding in any
file with a space in its name matched nothing and quietly vanished. One
percent-decode.

**A comment too long to post.** Findings render into a markdown table. A message
containing a newline or a pipe character breaks the table; a large result set
exceeds the comment size limit and the post fails outright. Either way you get a
green check and no visible findings. Now: cells sanitised, comment capped — and
capped by code points, so it can't split in the middle of a character and produce
something the API rejects.

## The pattern

Every one of those is a **fail-open**. And they share a shape: the failure was in
the *reporting path*, not the scanning path.

That's the bit I'd want to leave with people. When we think about a security gate
being wrong, we imagine the scanner missing a vulnerability — a detection problem,
someone else's to solve. In practice the scanner was fine. What broke was
everything around it: reading the output, matching it to the diff, rendering it,
posting it, deciding what the exit code should be.

That code is written by us, reviewed lightly because it's "just CI glue," and has
no tests. And it is exactly as load-bearing as the scanner.

**A security gate's characteristic failure mode is silence.** Worse than no
scanner, because a green scan is a clean bill of health somebody will cite in a
review — and the absence of findings is indistinguishable from the absence of
scanning.

## Two more, while we're here

The workflows pinned third-party actions to floating tags. Now every one is pinned
to an exact commit. A tag is mutable; the whole supply-chain argument you're
making with the scanner is undermined by trusting a moving reference in the thing
doing the scanning.

And the scan installed dependencies with lifecycle scripts enabled. That means
running arbitrary code from the very dependencies you are scanning for being
untrustworthy, inside a CI job, before you've decided whether to trust them.
Install with scripts disabled.

## Testing the thing that tests

Because these gates live as scripts embedded in workflow files, they're nearly
impossible to test in place. So they got extracted and run against fixtures — a
missing results file, an empty results array, a truncated diff, a failed scan
step, a message with a newline and a pipe in it — asserting that each one blocks
rather than passes.

Twenty-one cases. It's the least glamorous test suite in the project and I'd argue
for it hardest, because it's the only evidence that the gate can fail at all. Up
to that point, every piece of evidence we had about those scanners was that they
returned green — which was consistent with them working perfectly and equally
consistent with them being incapable of doing anything else.

If you have a gate you have never watched fail, you don't know whether it's a
gate. That's true of coverage checks, type checks, smoke tests and deploy gates,
and it's most true of security scanners, because they're the ones you're least
likely to trip by accident.

Go and break yours on purpose. It's twenty minutes, and either you'll confirm it
works or you'll have a much more interesting afternoon.
