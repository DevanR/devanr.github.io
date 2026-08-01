---
layout: post
title: "One Hostname, Two Services"
excerpt: "Putting a web app and its API behind a single same-origin load balancer deletes a whole category of browser problem. Here is what it costs, including the health check that must not move."
categories: articles
tags: [load-balancing, cloud-run, gcp, architecture, cors, websockets]
comments: false
share: true
modified:
series: "Building it dark"
series_part: 2
---

The web app and the API had always been separate origins. Different hostnames,
one cookie shared across them, a real-time socket connection opening to the
second host, and CORS headers doing the heavy lifting in between.

It worked. It also meant every browser vendor's next decision about cross-site
cookies was a scheduled incident on somebody's calendar.

So the last piece of the migration was an edge: one global HTTPS load balancer,
**one hostname**, path-routed to two container services.

| Path | Goes to |
| --- | --- |
| `/api/*` | the API service |
| `/socket.io/*` | the API service |
| everything else | the web app |

Same origin. No CORS. A first-party cookie. One certificate. The browser only
ever talks to one host, and it stops being a participant in your architecture.

That's the whole benefit, and it's a big one. The rest of this post is the price,
because nobody writes that part down.

## Price one: the API's entire REST surface has to move

If `/api/*` routes to the API service, then the API has to serve its routes under
`/api`. All of them.

We got lucky here — the application already supported a path prefix as a
configuration value, and every handler registered at `${PREFIX}/…`. So the change
was one environment variable per environment and no application code at all.

If your API doesn't already have that seam, budget for it properly. Retrofitting
a prefix onto a router that hardcodes its paths is not a config change, it's a
day of find-and-replace with a bad failure mode: the routes you miss return 404
through the load balancer and 200 when you test the service directly.

## Price two: the health check must *not* move

This is the one I'd want someone to tell me before I started.

Two things call the health endpoint, and neither of them goes through the load
balancer:

1. The container platform's own startup and liveness probe, which hits the
   service directly.
2. The deploy smoke test, which brings a new revision up at zero traffic on a
   private tagged URL and asserts it's healthy before promoting it.

Turn on a global `/api` prefix and both of those break at once — the probe fails,
so the revision never becomes ready, so the deploy that introduced the prefix
fails in a way that looks like the application is broken.

So health stays deliberately unprefixed, as an explicit carve-out, while every
other route moves. That is an inconsistency, and inconsistencies get tidied away
by well-meaning people six months later. It needs a comment at the definition
explaining what depends on it, not just a line in a design doc.

The general rule: **before you move a path, enumerate everything that calls it
without going through your new edge.** Probes, smoke tests, uptime monitors,
internal service-to-service calls, and the load balancer's own health checks all
bypass the routing layer you're about to change.

## Price three: root-path collisions are the actual reason for the prefix

The prefix wasn't chosen for tidiness. It was forced.

Both services independently owned routes at the same top-level paths — a file
route, a CSP-report sink, a health endpoint. Under two hostnames that's fine;
they never meet. Under one hostname, exactly one of them can win.

In our case the file route belongs to the web app, which proxies object storage
server-side. The API's same-named routes now live under the prefix. The CSP sink
is the web app's; the API's is under the prefix too.

This is the kind of conflict that is glaringly obvious in a routing table and
completely invisible in a code review of either repository. Neither diff is wrong.
The collision only exists in the space between them.

If you're planning a same-origin edge, do this first: list every top-level path
each service registers, put them in one table, and look for the overlap. Ten
minutes, and it tells you whether you need a prefix and where.

## Price four: the client has to learn that its bases differ

The web app had a single base URL for everything — REST, socket, uploads.

Under the edge, they diverge. REST is the host plus the prefix. The socket base is
the bare host, because the socket path is carved out at the root of the URL map.
Uploads are the host plus their own path. One hostname, three different bases.

We split the REST base out as its own configuration value — and made it
**optional, falling back to the existing socket base when unset**. That detail did
more work than it looks like.

During a dark migration, the config change and the image build roll through two
environments on independent schedules. An optional value with a sane fallback
means the new configuration is *inert* on any image built before the split, and
the new image behaves exactly as it did before on any environment that hasn't set
the value. Neither half of the change can break the other half's environment.

That's a cheap habit worth generalising: **when a config change and a code change
have to meet, make the config optional so they can arrive in either order.**

## Is it worth it?

You are taking on real infrastructure: a URL map, two backend services, a managed
certificate with its own provisioning lifecycle, a WAF policy, and a set of
failure modes that live entirely at the edge and never reach your application
logs. (That last one has its own post in this series — it turns out we couldn't
see any of them.)

In exchange you delete cross-origin cookies, CORS preflights, and an entire class
of "it works for me but not in Safari" from your future.

My rule of thumb: if you have session cookies and websockets, take the trade. If
you have a static front end talking to a public API with tokens, don't bother —
you're buying infrastructure to solve a problem you don't have.

What forced your hand into a same-origin edge, if it did — cookies, or something
else?
