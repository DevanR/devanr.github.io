---
layout: post
title: "Notes on Test-Driven Development as Pragmatic Deliberate Practice"
excerpt: ""
categories: articles
tags: [tdd, deliberate-practice]
comments: false
share: true
modified:
---

Book [1]

Test Driven Development has really helped me become a better programmer.  And
there is no one better to learn it from from JB Rainsberger himself.  Here are
some of my notes on two of my favourite topics, deliberate practice and TDD.

Fix bugs test first.

After reviewing the literature, I identified number of ways that experts in different fields learn:

* They engage in deliberate practice, so that each opportunity for practice has a goal and evaluation criteria.
* They compile an extensive experience bank.
* They obtain feedback that is accurate, diagnostic, and reasonably timely.
* They enrich their experiences by reviewing prior experience to derive new insights and lessons from mistakes.

Goals for TDD practise sessions.

* Test-drive the integration point to a library you haven’t worked with before.
* Isolate more of your code from the integration point to a framework.
* Write fewer tests that need a framework testing library (like Robolectric, NUnitASP, rspec-rails, or JSFUnit) and more that use the plain testing framework (plain JUnit, RSpec, or pytest).
* Reduce the time it takes to write the next test.

Evaluation criteria for TDD practise sessions.

* Did I build this part of the system more easily than usual?
* Do the names in this part of the system make it easier for others to understand how to change this code?
* Can I extend this part of the system more easily by only adding code, rather than having to change it?
* Does the setup code that I need to run my tests involve only the parts of the system that I’ve just designed?
* If I have multiple assertions in a test, do I consider this very strongly related to each other?
* Did the pace at which new tests passed feel fast to me? or at least faster than before?

##### Thoughts

I think it boils down to having the discipline to invest in the time and
opportunity to practice.

[1]: https://blog.jbrains.ca/permalink/test-driven-development-as-pragmatic-deliberate-practice
