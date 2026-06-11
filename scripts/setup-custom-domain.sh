#!/usr/bin/env bash
# Point your own domain at the v2 GitHub Pages site (no username in the link).
# Usage: bash scripts/setup-custom-domain.sh www.petsittersclub.co.uk
set -euo pipefail

cd "$(dirname "$0")/.."

DOMAIN="${1:-}"
if [[ -z "${DOMAIN}" ]]; then
  echo "Usage: bash scripts/setup-custom-domain.sh www.yourdomain.co.uk"
  echo ""
  echo "Suggested names for Pet Sitters Club:"
  echo "  www.petsittersclub.co.uk"
  echo "  www.petsittersclublondon.co.uk"
  exit 1
fi

DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN%/}"

set -a
# shellcheck disable=SC1091
[[ -f scripts/.env ]] && source scripts/.env
set +a

: "${GITHUB_USER:?Set GITHUB_USER in scripts/.env}"

python3 - <<PY
from pathlib import Path
import re

domain = "${DOMAIN}"
config = Path("config.js")
text = config.read_text()
text = re.sub(r"customDomain:\s*'[^']*'", f"customDomain: '{domain}'", text)
text = re.sub(
    r"publicBookingUrl:\s*'[^']*'",
    f"publicBookingUrl: 'https://{domain}/book/'",
    text,
)
config.write_text(text)
Path("CNAME").write_text(domain + "\\n")
print(f"Updated config.js and CNAME → {domain}")
PY

if grep -q '^CUSTOM_DOMAIN=' scripts/.env 2>/dev/null; then
  sed -i '' "s|^CUSTOM_DOMAIN=.*|CUSTOM_DOMAIN=${DOMAIN}|" scripts/.env
else
  echo "CUSTOM_DOMAIN=${DOMAIN}" >> scripts/.env
fi

echo ""
echo "Next steps (one-time):"
echo ""
echo "1. Buy the domain if you have not already (${DOMAIN})."
echo ""
echo "2. At your domain registrar, add DNS:"
echo "   CNAME   www   →   ${GITHUB_USER}.github.io"
echo "   (For the bare domain without www, add GitHub's four A records — see link below.)"
echo ""
echo "3. GitHub → pet-sitting repo → Settings → Pages → Custom domain → enter: ${DOMAIN}"
echo ""
echo "4. Publish: bash scripts/deploy-github-v2.sh \"Custom domain\" && bash scripts/publish-v2-preview.sh"
echo ""
echo "Your share link will be: https://${DOMAIN}/book/"
echo "DNS help: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site"
