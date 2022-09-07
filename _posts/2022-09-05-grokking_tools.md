---
layout: post
title: "Grokking Codebases quickly"
excerpt: ""
categories: articles
tags: [notes, visualisation]
comments: false
share: true
modified:
---

I recently I had to work with a large legacy codebase. It was especially
confusing as there was no documentation available. In order to get myself up to
speed as quickly as possible, I invested some time in finding some tools to aid
me in understanding the architecture of the codebase.

Here are some tools I found which might be useful to you:

1. [gource](https://gource.io/)

    A really cool visualisation library that lets you generate a movie of all the
    commits on a codebase in real-time. It's not very scientific but I like that it
    gives you an overall sense of the history of a project. It visualises the the
    authors as well as the file types committed.

2. [PySnooper](https://github.com/cool-RR/PySnooper)

    A useful tool when working with a legacy codebase and you don't have the ability
    to load the entire beast into an IDE. Allows you to tactically insert a single
    debug line and get feedback immediately.

3. [py-spy](https://github.com/benfred/py-spy)

    This tool works with a running process. You point it to the process PID and it
    can generate [flamegraps](https://github.com/brendangregg/FlameGraph) as well as
    real-time top visualition. It is especially useful if you do not have access to
    any source code and you're trying to figure out what a process is doing.

4. [Speedscope](https://github.com/jlfwong/speedscope)

    This is tool is an alternative to flamegraphs. It's an interactive, web-based
    viewer for performance profiles. It allows to you to drill down into a process
    to see where its spending its CPU cycles, RAM or time. I used it to profile
    my Django tests to see if there was an opportunity to speed them up.
