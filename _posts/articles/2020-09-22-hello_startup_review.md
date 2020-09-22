---
layout: post
title: "Book Review: Hello Startup"
excerpt: ""
categories: articles
tags: [notes, startup]
comments: false
share: true
modified:
---

I recently finished a wonderful book on the technical decisions of building a
startup. I personally found the bits on picking a tech stach most interesting.

#### Picking a Tech Stack

A good tech stack is one that scales faster than the people required to
maintain it.

The current stack will definitely be wrong for the future, It just needs to get
us there. Iteration is the key.

Pick a list of popular languages. You can quickly shorten this list by applying
three filters: problem fit, programming paradigm, and performance requirements.

If you’re using a web framework to build something important to your
business—something that’s more than a prototype—the best choice is usually a
modular full stack framework. That way, you get the best of both worlds: a
documented, community supported, open source framework where the defaults do a
good job of handling most use cases, plus the ability to plug in custom
libraries for a few special cases.

Django is for CRUD.
Node.js is for realtime applications.

Consider splitting the web app by language and purpose.
