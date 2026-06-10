#!/usr/bin/env bash
# Push the latest site to the GitHub Pages mirror.
# Netlify stays the primary site; this is the parallel GitHub stream.
set -euo pipefail

cd "$(dirname "$0")/.."

# Load token/user from scripts/.env
set -a
# shellcheck disable=SC1091
source scripts/.env
set +a

: "${GITHUB_TOKEN:?Set GITHUB_TOKEN in scripts/.env}"
: "${GITHUB_USER:?Set GITHUB_USER in scripts/.env}"
: "${GITHUB_REPO:=pet-sitting}"

git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" add -A
git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" commit -m "${1:-Update site}" || echo "Nothing to commit"
git push "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git" main
echo "Pushed. Live shortly at: https://${GITHUB_USER}.github.io/${GITHUB_REPO}/"
