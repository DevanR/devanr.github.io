---
layout: post
title: "Two Credentials, and the Weaker One Wins"
excerpt: "We replaced a long-lived session cookie with a credential minted per run, then left the old path in as a harmless fallback. It was not harmless — it was an outage with a thirty-day fuse."
categories: articles
tags: [security, release-engineering, ci-cd, secrets, incidents]
comments: false
share: true
modified:
series: "Building it dark"
series_part: 5
---

The deploy gate needed to prove more than "the service answers." The application's
core feature is real-time, so a candidate revision that serves a healthy HTTP
response while its socket layer is broken is exactly the deploy we most wanted to
stop.

So the gate grew a second, deeper assertion: log in as a dedicated smoke user,
open a real-time connection, exercise the contract, and only then promote. It
gates every promotion, production included.

That assertion needs a credential. This is the story of the credential, and it's
the one lesson from the whole project I'd most like to have learned from someone
else's post.

## Three versions

**Version one: a stored session cookie.** A valid session, captured once by hand
and put in the secret manager. Simple. Worked immediately. Long-lived secrets in a
CI system are a known smell, but it unblocked the gate.

**Version two: mint a session per run.** The pipeline authenticates with the smoke
user's password and gets a fresh session for that run, then revokes it. Nothing
long-lived, nothing to rotate, nothing to expire quietly.

Better in every way. We shipped it, cut both environments over, and deleted the
cookie secrets.

**Version three: delete the cookie code path.** Which is where this gets
interesting, because at the time it looked like tidying up.

## Why the "dormant" path was not dormant

The code still accepted a cookie. Both environments were configured with a
password. Every run minted its own session. The cookie branch was unreachable in
practice, and I'd have described it as inert.

Two things made it a live hazard.

**First: the cookie won.** In the precedence order, a cookie supplied alongside a
password was *preferred*. So re-creating that secret — in a fork, in a new
environment, by an operator following documentation we hadn't finished updating —
would silently move that environment back onto the old credential. Nothing reports
a downgrade. There is no log line for "using the weaker of two available
credentials," because from the code's point of view nothing unusual happened.

**Second: that credential dies on a timer.** The application enforces a hard
thirty-day cap on session lifetime. So a stored cookie is not merely weaker, it is
a scheduled failure. Set it today, and in a month the gate stops working.

And here's the bit that turns an inconvenience into a proper incident: when it
fails, the socket login returns a negative acknowledgement. Which is **byte-for-byte
identical** to what a genuinely broken build returns.

So the failure mode is: on a date nobody chose, weeks after the change that caused
it, a production deploy is blocked with a symptom that says the application is
broken. The on-call engineer starts by reading the pull request being deployed —
which is fine — and the actual cause is a secret that someone re-created a month
ago in good faith.

That is precisely the class of failure this entire workstream existed to remove.
A scheduled outage with a misleading symptom.

We also found that several places in the repository still instructed an operator to
create exactly that secret — including the description of the ticket that had
*automated its replacement*. Documentation rot isn't cosmetic when the document
is a runbook. It's a loaded instruction.

## The fix

Delete the branch. Specifically:

- A cookie supplied alongside a password is **ignored**, not preferred.
- A cookie supplied **alone fails closed** with an error, rather than resolving to
  a working credential mode. A stale secret in a fork cannot present as
  functioning configuration.
- The error message **names both real secrets explicitly**, per environment.
  This one is subtle and I think it's the sharpest detail in the change: the
  environments' secret names differ by a suffix, and a reasonable operator guessing
  the pattern produces a name the workflow never reads. That guess doesn't fail
  loudly — it produces an environment where the gate soft-passes while everyone
  believes it is armed. An error message that guesses on your behalf is worth more
  than one that's merely accurate.
- Every instruction telling someone to create the old secret is gone.

Net effect: about forty lines added, no behaviour change whatsoever for a
correctly configured environment. The change is entirely about which *incorrect*
configurations are now impossible.

## The lesson

**A deprecated authentication path is not dormant while the code still accepts it.**

"We're not using that any more" is a statement about today's configuration. It is
not a statement about the code. Configuration changes — during a migration, it
changes constantly, in environments you didn't create, by people reading
documentation you forgot to update.

And the asymmetry that makes this genuinely dangerous: if the weaker credential
*loses* the precedence order, a leftover secret is harmless clutter. If it *wins*,
the same leftover secret is a downgrade with no alarm attached. Same code, same
config, opposite risk — decided by a line of precedence logic nobody reviewed as a
security decision.

So: delete the old path in the same change that replaces it. If you genuinely
can't, at minimum make the weaker option lose, and make choosing it say so out
loud.

Otherwise you haven't deprecated anything. You've scheduled an incident and
written the misleading symptom yourself.

Have you got a fallback path in your system that would win if both were present?
