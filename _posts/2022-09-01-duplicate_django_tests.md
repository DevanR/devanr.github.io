---
layout: post
title: "Detecting Duplicate Django Tests"
excerpt: ""
categories: articles
tags: [notes, django, tdd, script]
comments: false
share: true
modified:
---

While improving the test coverage of a legacy Django code base, the question of
duplicate tests was raised. This particular code base moved towards using
end-to-end tests sometime in its past because the business logic became to
tangled to unit test.  As a result, with each new feature, more and more
end-to-end tests were piled on.

As part of an initial survey, the question was raised as to how many of our
tests were testing duplicated parts of the code base. And whether we could
eliminate any duplicate tests to speed up our runs.

To find out, I conducted an experiment to see what was the minimum number of
test I could run to keep the same level of coverage.

I first ran the entire test suite with coverage and made sure to enable dynamic
contexts. This creates an sqlite database which I could then mine. The database
provides the total number of tests as well as the lines tested by each test.
Also, we know the overall percentage of coverage as provided by the coverage
report.

The interesting bit, is how to select the minimum number of tests to get the
same percentage of coverage. Turns out, this is known as the set cover problem.
After going down the rabbit-hole if P vs NP algorithms, I eventually settled on
a [greedy approach](http://www.martinbroadhurst.com/greedy-set-cover-in-python.html) for
best results.

After writing a python script to extract the set of tests. I could then re-run
coverage with that set of tests to verify that the percentage of coverage is the
same.

One interesting finding is was that with this particular code-base, I could
achieve the same percentage of coverage with one quarter of the number of tests.

You can download my python script [here](/assets/script/duplicate_tests.py).
