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
marker = "        var live = 'https://rashmiakanksha1-blip.github.io/pet-sitting/';"
if marker in html:
    html = html.replace(
        marker,
        "        var live = 'https://rashmiakanksha1-blip.github.io/pet-sitting/availability/';",
    )
index.write_text(html)

Path("availability.html").write_text("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="0; url=availability/" />
  <title>Check availability</title>
  <script>location.replace('availability/');</script>
</head>
<body>
  <p><a href="availability/">Open availability calendar</a></p>
</body>
</html>
""")

book_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="0; url=availability/" />
  <title>Book pet sitting</title>
  <script>location.replace('availability/');</script>
</head>
<body>
  <p><a href="availability/">Book pet sitting</a></p>
</body>
</html>
"""
Path("book.html").write_text(book_html)

Path("v2/index.html").parent.mkdir(parents=True, exist_ok=True)
Path("v2/index.html").write_text("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="refresh" content="0; url=../availability/" />
  <title>Redirecting…</title>
  <script>location.replace('../availability/');</script>
</head>
<body>
  <p><a href="../availability/">Open availability calendar</a></p>
</body>
</html>
""")
PY

git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" add availability availability.html book.html v2
git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" commit -m "Publish v2 at /availability" || echo "Nothing to commit"
git push "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO}.git" main

git checkout "${RETURN_BRANCH}"
echo "Live calendar: https://${GITHUB_USER}.github.io/${REPO}/availability/"
