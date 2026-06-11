#!/usr/bin/env bash
# Publish the v2 branch as the live GitHub Pages site (root + /book/).
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
# shellcheck disable=SC1091
source scripts/.env
set +a

: "${GITHUB_USER:?Set GITHUB_USER in scripts/.env}"
REPO="${GITHUB_REPO:-pet-sitting}"
RETURN_BRANCH="$(git branch --show-current)"

if ! git rev-parse --verify v2 >/dev/null 2>&1; then
  echo "Missing v2 branch."
  exit 1
fi

git checkout main

for file in index.html config.js auth.js shared.js; do
  git show "v2:${file}" > "${file}"
done

rm -rf book availability v2
mkdir -p book

for file in index.html config.js auth.js shared.js; do
  git show "v2:${file}" > "book/${file}"
done

python3 - <<'PY'
from pathlib import Path

root_base = '  <base href="/pet-sitting/" />\n'
book_base = '  <base href="/pet-sitting/book/" />\n'
viewport = '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'

def add_base(path: Path, base_tag: str) -> None:
    html = path.read_text()
    if "<base " in html:
        return
    path.write_text(html.replace(viewport, viewport + base_tag, 1))

add_base(Path("index.html"), root_base)
add_base(Path("book/index.html"), book_base)

redirect = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="0; url=book/" />
  <title>Redirecting…</title>
  <script>location.replace('book/');</script>
</head>
<body>
  <p><a href="book/">Open Pet Sitters Club calendar</a></p>
</body>
</html>
"""
Path("availability.html").write_text(redirect.replace("Redirecting…", "Check availability"))
Path("book.html").write_text(redirect.replace("Redirecting…", "Book pet sitting").replace("Open Pet Sitters Club calendar", "Book pet sitting"))
Path("v2/index.html").parent.mkdir(parents=True, exist_ok=True)
Path("v2/index.html").write_text(redirect)
PY

git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" add \
  index.html config.js auth.js shared.js book availability.html book.html v2
git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" commit -m "Publish v2 as live site" || echo "Nothing to commit"
git push "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO}.git" main

git checkout "${RETURN_BRANCH}"
echo "Live v2 site: https://${GITHUB_USER}.github.io/${REPO}/book/"
