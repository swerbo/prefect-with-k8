#!/bin/bash
set -x

if [ "$IS_PIP_PACKAGE" ]; then
    echo "IS_PIP_PACKAGE environment variable found."
    pip install "git+https://$GITHUB_ACCESS_TOKEN@github.com/$REPO_NAME.git@$GIT_BRANCH"
fi

# Run extra commands
exec "$@"