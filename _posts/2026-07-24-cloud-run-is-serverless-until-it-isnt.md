---
layout: post
title: "Cloud Run Is Serverless Until It Isn't"
excerpt: "Bringing a client's application to production on Google Cloud Run, and the networking and bootstrapping snags a serverless platform doesn't warn you about."
categories: articles
tags: [cloud-run, gcp, infrastructure, opentofu, release-engineering]
comments: false
share: true
modified:
---

I recently took a client's application from nothing to a real production
deployment on Google Cloud Run — stage and prod, infrastructure as code, secrets
managed, the works. Cloud Run is a lovely platform to say yes to. You hand it a
container, it hands you a URL, and the scaling is somebody else's problem.

Then the real system arrives and the word "serverless" quietly stops meaning
"no infrastructure." It means "different infrastructure, and it's still yours."

Here are the parts that actually took the time. None of them were the container.

## The networking you thought you'd escaped

The first wall was the database.

The app talks to a managed MongoDB, and that database only accepts connections
from a known set of IP addresses. Reasonable. Except a Cloud Run service, by
default, egresses from a shared, ever-changing pool of Google IPs. There is no
address to put on the allowlist.

So the serverless service that was supposed to free me from networking needed:
a VPC connector, direct VPC egress, and a Cloud NAT with a *static* external IP —
one stable address the database could trust. The moment you need a predictable
source IP, you are back to owning a network.

And once you own a network, you own its capacity. I sized the egress subnet at a
/28 — sixteen addresses, surely plenty for one service. It wasn't. Direct VPC
egress consumes addresses faster than the intuition suggests, and under load the
subnet ran dry. Grew it to a /26 and the problem disappeared. That is a very
old-fashioned lesson — *subnet too small* — arriving inside a very modern
platform.

The trade-off worth naming: serverless sells you out of capacity planning right
up until you touch something with an IP allowlist. Then you get all of it back
at once, and it's better to design for it on day one than to discover it when
production connections start getting refused.

## Everything has a bootstrapping order

The subtler class of problem was ordering. Infrastructure as code loves to
describe the finished state — every service, every identity, every permission,
all present and referring to each other. Real infrastructure has to be *born*,
and at birth half of those things don't exist yet.

Three of these bit me in the same week.

**The safe-rollout gate.** I'd built a blue-green style deploy: bring the new
revision up alongside the old one, smoke-test it, shift traffic only once it's
proven. Lovely — except it works by comparing against the *current good
revision*. On the very first deploy of a brand-new service, there is no current
revision to fall back to. The safe path can't run because the thing that makes it
safe hasn't been created yet. The fix was to detect that case and degrade
gracefully to a plain apply for the first deploy, then let the safe path take
over once a baseline exists.

**The CI identity.** The deploy pipeline runs as a service account, and that
account needs permission to act as each service's runtime identity. I'd listed
the production runtime identity in that grant — before the production service
account existed. The grant refused, because you can't reference an identity that
hasn't been created. The answer was to defer it: leave production out of the list
until its service account is actually stood up, then admit it.

**The trust between repos and the cloud.** Deploys authenticate with workload
identity federation rather than long-lived keys, which means each application
repository has to be explicitly admitted to a shared identity provider. Stand up
a new environment and that trust has to be re-established, in order, before
anything can deploy at all.

The pattern underneath all three is the same: your infrastructure code has a
cold-start problem, and the default bug is *assuming the thing already exists*.
The finished-state description is correct for every day except the first one, and
the first one is the day you're actually watching.

## The unglamorous safety net

The last thing that earned its keep was the least clever: a written cutover
runbook and a set of smoke tests treated as a contract.

Not smoke tests as "does the health check return 200." Smoke tests as an explicit
list of the things that must be true after a deploy — the service answers, it
reaches the database, the real-time channel connects — codified so the deploy
itself can check them, and a human following the runbook can check the same list
by hand during a cutover. When the switch from the old environment to the new one
finally happened, the interesting part was how boring it was. That was the point.

## What I'd tell the version of me who started

Cloud Run genuinely removes a lot of work. It does not remove the network, the
identities, or the order those things have to come alive in. If you're planning a
similar stand-up, spend your design time on the parts that aren't serverless:

- Decide your egress story *before* the first database connection is refused —
  and size the subnet with room to spare.
- Assume every "reference" in your IaC will, at some point, point at something
  that doesn't exist yet. Make the first deploy a first-class case, not an
  afterthought.
- Write the cutover down and make the deploy prove its own success. A boring
  switch-over is a feature you build on purpose.

None of this is exotic. That's rather the point — the platform is new, but the
things that bite are the same things that always bite. Serverless just changes
where you meet them.
