# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Jekyll-based static website/blog (devanr.github.io) deployed on GitHub Pages. The site uses the "So Simple Theme" by mmistakes as a remote theme and focuses on technical articles covering software development, infrastructure, and DevOps topics.

## Development Commands

### Environment Setup
```bash
# Install Ruby via rbenv (if not already installed)
brew install rbenv ruby-build
rbenv init
rbenv install -l
rbenv install <latest-2.x-version>
rbenv local <version>

# Install dependencies
gem install bundler
bundle install
```

### Development Server
```bash
# Start Jekyll development server with live reload
bundle exec jekyll serve --livereload

# The site will be available at http://localhost:4000
```

### Building the Site
```bash
# Build the site to _site/ directory
bundle exec jekyll build

# Clean generated files
bundle exec jekyll clean
```

## Architecture and Structure

### Content Management
- **Posts**: All blog posts are in `_posts/` with naming format `YYYY-MM-DD-title.md`
- **Pages**: Static pages are in root directories (`about/`, `articles/`, `publications/`, `search/`)
- **Data**: Site configuration and navigation in `_data/`
- **Layouts**: Page templates in `_layouts/`
- **Includes**: Reusable components in `_includes/`

### Post Front Matter Structure
```yaml
---
layout: post
title: "Post Title"
excerpt: "Brief description"
categories: articles
tags: [tag1, tag2, tag3]
share: true
comments: false
modified: YYYY-MM-DD  # Optional
---
```

### Theme Configuration
- Uses remote theme: `mmistakes/so-simple-theme`
- Main configuration in `_config.yml`
- Custom styles in `_sass/` directory
- Theme documentation: https://github.com/mmistakes/so-simple-theme

### Site Structure
- **Generated content**: `_site/` (excluded from git)
- **Assets**: `assets/` contains CSS, JavaScript, fonts, and PDFs
- **Images**: `images/` for site media files
- **Navigation**: Configured in `_data/navigation.yml`

### GitHub Pages Deployment
- Uses `github-pages` gem (version 219)
- Automatically deploys from main branch
- Jekyll plugins limited to GitHub Pages whitelist