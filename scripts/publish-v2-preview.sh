#!/usr/bin/env bash
# Copy the v2 branch into /v2 on main so GitHub Pages serves a preview URL
# without replacing the live Version 1 site.
set -euo pipefail

cd "$(dirname "$0")/.."

set -a
# shellcheck disable=SC1091
source scripts/.env
set +a

: "${GITHUB_USER:?Set GITHUB_USER in scripts/.env}"
REPO="${GITHUB_REPO:-pet-sitting}"
PREVIEW_BASE="/${REPO}/v2/"
RETURN_BRANCH="$(git branch --show-current)"

if ! git rev-parse --verify v2 >/dev/null 2>&1; then
  echo "Missing v2 branch."
  exit 1
fi

git checkout main
rm -rf v2
mkdir -p v2

for file in index.html config.js auth.js shared.js; do
  git show "v2:${file}" > "v2/${file}"
done

python3 - <<'PY'
from pathlib import Path

index = Path("v2/index.html")
html = index.read_text()
base_tag = '  <base href="/pet-sitting/v2/" />\n'
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
        "        var live = 'https://rashmiakanksha1-blip.github.io/pet-sitting/v2/';",
    )
index.write_text(html)
PY

git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" add v2
git -c user.email="petsittersclublondon@gmail.com" -c user.name="Pet Sitters Club" commit -m "Publish v2 preview at /v2" || echo "Nothing to commit"
git push "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO}.git" main

git checkout "${RETURN_BRANCH}"
echo "V2 preview: https://${GITHUB_USER}.github.io/${REPO}/v2/"
