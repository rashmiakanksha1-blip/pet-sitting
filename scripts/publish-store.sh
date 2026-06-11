#!/usr/bin/env bash
# Push data/store.json live (main) and mirror to book/data/ for /book/ share link.
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
# shellcheck disable=SC1091
source scripts/.env
set +a

: "${GITHUB_TOKEN:?Set GITHUB_TOKEN in scripts/.env}"
: "${GITHUB_USER:?Set GITHUB_USER in scripts/.env}"
REPO="${GITHUB_REPO:-pet-sitting}"
RETURN_BRANCH="$(git branch --show-current)"

git stash push -m "publish-store" -- data/store.json 2>/dev/null || true
git checkout main

mkdir -p book/data
cp data/store.json book/data/store.json
[[ -f data/inquiries.json ]] && cp data/inquiries.json book/data/inquiries.json

git add data/store.json book/data/store.json
[[ -f book/data/inquiries.json ]] && git add book/data/inquiries.json

git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" \
  commit -m "${1:-Update live calendar}" || echo "Nothing to commit"

git push "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO}.git" main

git checkout "${RETURN_BRANCH}"
git stash pop 2>/dev/null || true

echo "Live calendar updated: https://www.petsittersclub-london.com/book/"
