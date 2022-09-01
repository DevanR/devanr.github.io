# Install Rbev
brew install rbenv ruby-build
rbenv init
curl -fsSL https://github.com/rbenv/rbenv-installer/raw/main/bin/rbenv-doctor | bash
https://github.com/rbenv/rbenv

# Install latest Ruby version for 2
rbenv install -l
rbenv install <version>

# Configure local env
cd <working-directory>
rbenv local <version>
restart shell

# Install gem
gem install bundler
build install

# Install Jekyll
bundle exec jekyll serve
