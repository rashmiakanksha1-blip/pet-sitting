#!/usr/bin/env bash
# Copy the v2 branch into /availability on main so GitHub Pages serves a clean URL
# without replacing the live Version 1 site at the repo root.
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
# shellcheck disable=SC1091
source scripts/.env
set +a

: "${GITHUB_USER:?Set GITHUB_USER in scripts/.env}"
REPO="${GITHUB_REPO:-pet-sitting}"
PREVIEW_BASE="/${REPO}/availability/"
RETURN_BRANCH="$(git branch --show-current)"

if ! git rev-parse --verify v2 >/dev/null 2>&1; then
  echo "Missing v2 branch."
  exit 1
fi

git checkout main
rm -rf availability v2
mkdir -p availability v2

for file in index.html config.js auth.js shared.js; do
  git show "v2:${file}" > "availability/${file}"
done

python3 - <<'PY'
from pathlib import Path

index = Path("availability/index.html")
html = index.read_text()
base_tag = '  <base href="/pet-sitting/availability/" />\n'
if "<base " not in html:
    html = html.replace(
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n' + base_tag,
        1,
    )
index.write_text(html)

BOOK = "https://petsittersclublondon.netlify.app/book"
redirect = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="0; url={BOOK}" />
  <title>Redirecting…</title>
  <script>location.replace('{BOOK}');</script>
</head>
<body>
  <p><a href="{BOOK}">Open Pet Sitters Club calendar</a></p>
</body>
</html>
"""
Path("availability.html").write_text(redirect.replace("Redirecting…", "Check availability"))
Path("book.html").write_text(redirect.replace("Redirecting…", "Book pet sitting").replace("Open Pet Sitters Club calendar", "Book pet sitting"))
Path("v2/index.html").write_text(redirect)
PY

git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" add availability availability.html book.html v2
git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" commit -m "Publish v2 at /availability" || echo "Nothing to commit"
git push "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO}.git" main

git checkout "${RETURN_BRANCH}"
echo "Share this link: https://petsittersclublondon.netlify.app/book"
