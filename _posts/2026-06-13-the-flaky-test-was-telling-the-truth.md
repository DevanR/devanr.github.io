---
layout: post
title: "The Flaky Test Was Telling the Truth"
excerpt: "An intermittent mobile login test was going red on unrelated pull requests. Underneath it were two genuine defects — a navigation race in the app, and a CI machine we'd overprovisioned into failure."
categories: articles
tags: [testing, e2e, mobile, ci-cd, flaky-tests]
comments: false
share: true
modified:
series: "Earning the right to move"
series_part: 6
---

We added an end-to-end login test to the mobile app — a real emulator, a real
install, a deep link back into the app, all the way to the authenticated screen.

It was intermittently red. Worse, it was red on pull requests that had nothing to
do with it, including one that only touched CI configuration and merely inherited
the workflow.

That's the moment the team's patience runs out, and the pressure to quarantine it
becomes very reasonable-sounding. Mark it non-blocking, move on, revisit later.

We didn't, and it took two fixes, and both of them were real bugs.

## Bug one: a race that real users mostly dodged

The deep-link login callback did something that looks entirely sensible: before
navigating into the app, check that we're currently on the login screen.

On a cold start, the app's initialisation finds no token and redirects to the
login screen — **asynchronously**. Meanwhile the deep link fires almost
immediately, stores the token, and connects. When the callback's continuation ran
before the redirect had settled, the path check was false, navigation never
happened, and the app sat on the unauthenticated screen holding a perfectly valid
session.

Real users rarely hit it. They tap through a web login, spend a few seconds there,
and come back to an app that has long since settled on the login screen. The
window is small.

The test hit it constantly, because clearing all state and immediately opening the
link compresses exactly the timing that real usage spreads out.

The fix removed the assumption rather than the race: a login-callback deep link
exists *only* to complete a login, so it now always navigates on success. No
dependence on where the app happened to be.

**That is a genuine defect that users would hit occasionally and never report
reproducibly.** "It said I was logged in but showed me the login page — I just
restarted it." Nobody files that ticket. It would have lived in the app
indefinitely, because the only thing capable of reporting it reliably was the test
everyone wanted to disable.

## Bug two: we'd given the machine too much

With the race fixed, the test failed again — earlier, at step one, before the deep
link was even involved.

The failure screenshot showed the device launcher with a system dialog: *process
system isn't responding*. Not our app. The operating system.

The boot log had been saying so all along: the emulator was configured with more
virtual CPUs than the nested virtualisation on the CI runner can actually
schedule. Cold boot plus install plus web-view launch created enough contention
to make the OS itself unresponsive, which backgrounded the app, so the login
screen never painted.

The fix was to give it **fewer** cores, not more, plus extra RAM headroom the
runner had spare.

I want to dwell on that for a second, because the instinct — mine included — is
that a resource-starved test needs more resources. Here, overcommitting the CPU
*was* the starvation. More cores would have made it worse, and it's the kind of
change that looks so obviously correct in review that nobody questions it.

So the comment in the config records the actual failure mode, in words, so the
next person to see a slow emulator doesn't cheerfully bump the cores back up.
**Write the cause into the config, not just the value.** A bare number invites
someone to tune it; a number with a one-line explanation of what breaks invites
them to think.

There was a second-order fix too. The flow dismissed the startup dialog once, up
front. The observed failure had a *second* dialog appear during the subsequent
wait, which nothing was watching for. Wrapping dismiss-and-wait in a retry handles
a recurring dialog instead of assuming one is all you get.

## What I take from it

**"Flaky" describes your response, not the test.** It's a label we apply when a
failure isn't reproducible on demand, and it does something quietly corrosive: it
reclassifies a signal as noise, and once something is noise you stop reading it.

Nearly every flake I've chased has turned out to be a real race, a real resource
limit, or a real ordering assumption. The test isn't unreliable. The system is
non-deterministic in a way you haven't characterised yet, and the test is the only
thing that noticed.

That said, a flaky test genuinely is worse than no test while it's flaky — not
because it's wrong, but because it trains the team to re-run rather than read. Two
red-then-green cycles and the reflex is set. So it does have to be fixed
*urgently*. The mistake is fixing it by making it quieter instead of by finding
out what it's saying.

One honest caveat: a single green run doesn't prove a flake is gone. That needs
several consecutive clean runs on the main branch, which is an observation you
schedule rather than something a merge can deliver. We tracked that separately and
left the box unticked, because ticking it would have been a lie.

Also worth saying: this one didn't reproduce on any developer machine. It was a
nested-virtualisation cold-boot problem specific to the CI runner. The evidence
was a screenshot and a boot log — which is a good argument for capturing both from
every failed end-to-end run, because for an entire category of failure they're the
only evidence you will ever get.

What's the last test your team quarantined, and does anyone remember why?
