---
layout: post
title: "Getting Django to work with React"
excerpt: ""
categories: articles
tags: [django, react]
comments: false
share: true
modified:
---

I am interested in combining the benefits of Django and React
in a single web application. Here are some notes on the topic.
My goal is not to create a web application but to understand
the mechanism of how this can be achieved.

##### Patterns

#### Option [1]

React in its own "frontend" Django app: load a single HTML template and let React manage the frontend (difficulty: medium)

### Backend - Django

- create a frontend app
- serve a view with a Html template that contains the React App

### Frontend - React

- create a React component that is loaded from the Html template
- React component fetches data via Django API/URL

The approach here seems straight forward but limited. The examples here do not
go into depth as to how data can be saved.

#### Option [2]

Django REST as a standalone API + React as a standalone SPA (difficulty: hard, it involves JWT for authentication)

### Backend - Django

- create a django project
- whitelist local React server for CORS
- create model migrations and corresponding data migrations

### Frontend - React

- create React project within Django project
- install a HTTP client to consume API (e.g. axios)
- create Service.js file to contain axios functions
- create custom component that instantiates API Service.js
- bind service to component, so that it can be called in Html

### REST API - django-restframework

- create API endpoints in urls.py
- create API methods in views.py (with @api_view decorator)
- re-use in-built HTTP responses
- create model serializers to convert Python objects into JSON for React consumption

### Cross Origin Resource Sharing (CORS)

- install CORS support as Django middleware to allow access to local React server

#### Option 3

Mix and match: mini React apps inside Django templates (difficulty: simple, but not so maintainable in the long run)

This raises two questions for me. Firstly, what would be the best way of
handling sessions with this setup?  Secondly, what is the advantage of having a
Python backend in the first place?  Would it be better to use Node instead?
What are the tradeoffs?

[1]: https://www.valentinog.com/blog/drf/
[2]: https://www.digitalocean.com/community/tutorials/how-to-build-a-modern-web-application-to-manage-customer-information-with-django-and-react-on-ubuntu-18-04
