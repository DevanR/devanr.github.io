---
layout: post
title: "Book Summary: Time Series Forecasting with Python"
excerpt: ""
categories: articles
tags: [summary, python, forecasting]
comments: false
share: true
modified:
---

I am interested in combining the benefits of Django and React
in a single web application. Here are some notes on the topic.
My goal is not to create a web application but to understand
the mechanism of how this can be achieved.

##### Part 1

#### Python

What are the libraries?

#### Time Series forecasting defined

- nomenclature
- definitions

#### Forecasting as a Supervised Learning problem

- classification
- regression
- sliding window (reframe)
- univariate time series
- multi variate time series
- one step forecast
- multi step forecast

#### Time Series forecasting defined

##### Part 2

#### Loading Data

- read_csv()
- Pandas series
- series.head()
- series.tail()
- series.size
- series[time_index]
- series.describe()

#### Basic Feature Engineering

- change the timeseries into something that can be digested by a supervised learning model
- in essence we select the best features
- we test by checking the results of all our features
- honestly, feels like spray and pray

#### Data Visualization

1. Line Plots.
2. Histograms and Density Plots.
3. Box and Whisker Plots.
4. Heat Maps.
5. Lag Plots or Scatter Plots.
6. Autocorrelation Plots.

- All the visualisation methods can be used to quickly glean information about
  the data

- Some linear time series forecasting methods assume a well-behaved
  distribution of observations (i.e. a bell curve or normal distribution)

- Comparing box and whisker plots by consistent intervals is a useful tool.
  Within an interval, it can help to spot outliers (dots above or below the
  whiskers). Across intervals, in this case years, we can look for multiple
  year trends, seasonality, and other structural information that could be
  modeled.
