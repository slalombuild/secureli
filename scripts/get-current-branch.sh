#!/usr/bin/env bash
set -exo pipefail
# This script detects the git branch name from the environment and
# transforms it into a shortened label for use by the build and deployment process.
# It also validates the social contract of having a github issue for each

# The value returned by this script is:
#   branch: the abbreviated, formatted branch name based on the story number, e.g. "abc1234" or "main"

# Format the branch name
if [ -z "$branch" ]; then
  if [ -n "$BITBUCKET_BRANCH" ]; then
    branch="${BITBUCKET_BRANCH}"
  elif [ -n ${GITHUB_REF_NAME} ]; then
    branch="${GITHUB_REF_NAME}"
  fi
  # Format the branch from "feature/abc-123-my-branch" to "abc123"
  branch=$(echo "$branch" | cut -d'/' -f2 | cut -d'-' -f1-2 | tr '[:upper:]' '[:lower:]' | sed 's/-//g ; s/_//g')

  echo "Branch has been set to $branch" 1>&2
else
  echo "Branch is already defined as $branch" 1>&2
fi

# Check if short name work
if [[ $branch == "main" || $branch =~ ^secureli[0-9][0-9][0-9]$ || $branch =~ ^dependabot* ]]; then
  echo "The branch name is a valid pattern."
else
  echo "error The branch name ${branch} does not meet naming requirements. It should look something like feature/secureli-123-mybranchname."
  exit 1
fi

echo "$branch"
