#!/usr/bin/env bash
# Push the v2 design branch (preview — not the live v1 site).
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
# shellcheck disable=SC1091
source scripts/.env
set +a

: "${GITHUB_TOKEN:?Set GITHUB_TOKEN in scripts/.env}"
: "${GITHUB_USER:?Set GITHUB_USER in scripts/.env}"
: "${GITHUB_REPO:=pet-sitting}"

current_branch="$(git branch --show-current)"
if [[ "$current_branch" != "v2" ]]; then
  echo "Switch to the v2 branch first: git checkout v2"
  exit 1
fi

git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" add -A
git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" commit -m "${1:-Update site v2}" || echo "Nothing to commit"
git push "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git" v2
echo "Pushed v2 branch. Enable GitHub Pages from the v2 branch to preview, or merge to main when ready."
