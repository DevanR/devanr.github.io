---
layout: post
title: "Understanding Django's Unit Test Process with Multiple Databases"
excerpt: ""
categories: articles
tags: [presentation, tdd]
comments: false
share: true
modified:
---

Django's process for running unit tests, especially when multiple databases are
involved, is both intricate and fascinating. In this post, we'll break down the
process step-by-step, from the moment you run `python manage.py test`.

## Command Execution
When you execute `python manage.py test`, Django's `manage.py` script first
locates your project's settings and initializes the Django environment. It then
locates the test command and executes it.


## Test Discovery
Django's built-in test discovery mechanism automatically searches for tests. By
default, it looks for files named `test*.py` in your project directories,
adhering to Python's standard `unittest` discovery rules.

## Database Selection
For a standard Django setup, tests use the default database. However, if your
application employs multiple databases, you have control over which databases
are used for each test:

- By default, tests target the default database.
- Use the `databases` attribute in the `TestCase` class to specify different databases for your tests.

## Test Database Creation
Django checks whether a test database needs to be created. This behavior can be
customized:

- A separate test database is created by default.
- Tests that don't require a database can use `SimpleTestCase` or `TransactionTestCase` with `databases=[]`.
- For multiple databases, Django creates a test database for each, typically prefixed with `test_`.

## Migrations
Migrations are applied to ensure the test database schema matches your
development environment. The `--keepdb` flag can be used to retain the test
database between runs, speeding up the process.

## Test Execution
Django uses the test runner defined in your settings (default:
`django.test.runner.DiscoverRunner`) to execute tests. Each test is run in
isolation within a database transaction, maintaining test independence.

## Test Database Destruction
Post-testing, Django destroys the test databases unless the `--keepdb` flag is
used. This ensures a fresh start for subsequent test runs.

## Test Results
The results, including the number of tests, assertions, failures, and errors,
are displayed after the tests are complete.

Key Takeaway: In projects with multiple databases, it's crucial to correctly
specify the `databases` attribute in your `TestCase` classes. This ensures
proper setup and usage of the necessary databases for your tests.

Understanding and configuring this process is vital for effective testing in
complex Django projects.

## Best Practices for Multiple Database Applications
When managing tests in applications that support multiple databases, it's
generally advantageous to encourage modules to primarily interact with a single
database wherever feasible. This approach simplifies the testing process and
enhances maintainability.

Additionally, it's important to be aware of the role of the Database Router's
`allow_migration` method. This method plays a critical role during the
migration phase, particularly when creating test databases. In scenarios
involving secondary databases with unmanaged models, a notable consideration
arises: you must manually create the schema and tables for these models. This
step is crucial for ensuring that your tests execute correctly and interact as
expected with these unmanaged database components.

Implementing these best practices can significantly streamline the testing
process in complex Django environments, ensuring more robust and reliable test
outcomes.

