---
layout: post
title: "You Can't Fake a Chat Room"
excerpt: "Why feature flags beat a more realistic staging environment when the risky feature is real-time chat."
categories: articles
tags: [release-engineering, feature-flags, testing]
comments: false
share: true
modified:
---

A product I've been working with had a familiar setup: the business team
doubled as QA. Every release, they'd bang on the latest build, report what
broke, and only then would it reach real users.

The idea on the table was to formalise it. Give the business team their own
"latest, passed UAT" version of the app, leave everyone else on stable. Two
channels. It sounds reasonable. It's the instinct most teams have.

It's also the wrong mechanism for the right goal. Here's the reasoning, because
the reasoning generalises well beyond this one product.

## Staging is a lie, and chat makes the lie obvious

The pitch for a separate "realer" testing version is always the same: staging
isn't real enough, so let's build something closer to production.

The trouble is that staging fidelity is a race you can't win. You can always
make it *more* real, and it will never *be* real. There's no real data graph, no
real concurrency, no real network conditions, no real spread of devices. For a
lot of CRUD apps you can get close enough and move on.

For chat you can't.

Chat's worst bugs are emergent. They only show up when real people are in real
rooms at real scale: two users typing at once, presence flapping on a flaky
mobile connection, a message broadcasting to the wrong room because of a race
nobody could trigger by hand. You don't find those by seeding a test database
with three fake users. You find them when humans are actually talking to each
other.

So the more I looked at "build a realer staging version," the more it read as
pouring effort into the wrong lever. You can polish staging forever and still
ship the bug.

## The goal was right; the mechanism was wrong

Strip the idea back and the goal is sound: *let a small, trusted group use the
latest version against real data before everyone else gets it.*

That's a good goal. The problem was the mechanism. "A separate version" means
two builds of the app running at once, and the moment you have two server
versions you have to decide what they talk to.

Share one production database and you've signed up for both versions agreeing on
the data shape at all times — every migration backward-compatible, forever. Give
them separate databases and your testers aren't on real data any more, which was
the entire point.

That's the wall. And it's a one-way door: get the migration discipline wrong on
a live database and you don't get to undo it.

The way out is to stop thinking about versions at all.

## One version, different switches

The industry settled this a while ago, and the answer is feature flags.

A feature flag is just an on/off switch in the database that decides who can see
a feature, evaluated without a redeploy. The code ships to everyone. It stays
asleep until you flip the switch, and you choose who the switch is on for.

That dissolves the whole problem. There's only one version of the app, so
there's no two-versions-fighting-over-one-database. The test group is on the
real product, the real data, real chat with real users — they're simply the only
ones who can see the new thing. When it's solid, you widen the switch. When it
breaks, you flip it off. Nobody outside the group ever knew.

Take emoji reactions on chat messages as the worked example. New feature, you
want only the internal team to see it first.

The flag is one record:

```js
{ name: "message_reactions", enabled: true, role_whitelist: ["staff"] }
```

"Reactions are live, but only for staff." The server is the part that actually
enforces it. When someone tries to react, the server asks the flag before doing
anything:

```js
async function add_reaction(data, user, socket, callback) {
  if (!isEnabled("message_reactions", user)) {
    return callback({ ok: false, error: "not_available" });
  }
  // ...save the reaction, broadcast it to the room...
}
```

The client just hides the button when the flag is off. But the *server* is the
bouncer — otherwise a clever user could flip their own switch. The client is for
looks; the server decides.

## Widening without breaking anyone

The interesting part is the rollout. Once the internal team is happy, you want
to let in 10% of real users, then more. The naive version looks like this, and
it's a trap:

```js
if (Math.random() * 100 < flag.rollout_percentage) { ... }  // don't
```

That re-rolls the dice on every check. A user at 10% would see reactions,
refresh, lose them, refresh, get them back. For a chat feature, getting kicked
out of a conversation mid-sentence is exactly the bug you can't ship.

The fix is to give each user a permanent number for that flag and compare
against it:

```js
const crypto = require("crypto");

function inRolloutBucket(flagName, user, percentage) {
  if (percentage <= 0) return false;
  if (percentage >= 100) return true;

  const hash = crypto.createHash("sha256")
    .update(`${flagName}:${user.id}`)
    .digest("hex");

  const bucket = parseInt(hash.slice(0, 8), 16) % 100;  // stable 0–99 for this user + flag
  return bucket < percentage;
}
```

Same user, same flag, same answer every time. And because it's a fixed number,
widening only ever *adds* people. Everyone in at 10% is still in at 25% — you
never yank the feature out from under someone who already has it. Putting the
flag name in the hash matters too: it means the same unlucky users aren't the
guinea pigs for every feature you ship.

The full evaluation is small:

```js
function isEnabled(flag, user) {
  if (!flag || !flag.enabled) return false;                               // kill switch wins
  if (flag.role_whitelist?.some(r => user.role.includes(r))) return true; // the test group
  return inRolloutBucket(flag.name, user, flag.rollout_percentage);       // everyone else
}
```

Three behaviours, and they're the three worth writing tests for. The kill switch
beats everything — flag off means off, even for staff, even at 100%. The
whitelist lets the test group in regardless of percentage. The rollout is stable
and only ever widens. Pin those three down and you can rewrite the hash later
without fear.

## The principle

Don't try to make staging real. Make production reversible.

A more realistic test environment is a depreciating asset — it costs more every
year and never reaches the thing it's imitating. A feature flag is a few days of
work and it changes the question you're asking. Instead of "did we catch every
bug before release," it's "can we contain and undo a bug after release." For
real-time features, where the worst bugs only exist in production anyway, that's
the only question that was ever going to hold up.

The business team still tests the latest version against real data. They're just
the people with the switch flipped on, not the people on a different island.
