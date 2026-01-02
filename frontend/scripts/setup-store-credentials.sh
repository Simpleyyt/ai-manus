#!/bin/bash
# Store Credentials Setup Script for AI Manus

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           AI Manus Store Credentials Setup                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}GitHub CLI (gh) is not installed. Please install it first.${NC}"
    echo "Visit: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}Please authenticate with GitHub first:${NC}"
    gh auth login
fi

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
    echo -e "${RED}Could not detect repository. Are you in a git repo?${NC}"
    exit 1
fi

echo -e "${GREEN}Repository: $REPO${NC}"
echo ""

# Function to set secret
set_secret() {
    local name=$1
    local value=$2
    echo "Setting $name..."
    echo "$value" | gh secret set "$name" --repo "$REPO"
    echo -e "${GREEN}✓ $name set successfully${NC}"
}

# Function to set secret from file
set_secret_from_file() {
    local name=$1
    local file=$2
    if [ -f "$file" ]; then
        echo "Setting $name from file..."
        base64 "$file" | gh secret set "$name" --repo "$REPO"
        echo -e "${GREEN}✓ $name set successfully${NC}"
    else
        echo -e "${YELLOW}⚠ File not found: $file${NC}"
    fi
}

echo "═══════════════════════════════════════════════════════════════"
echo "Setting up Android secrets..."
echo "═══════════════════════════════════════════════════════════════"

# Android Keystore
KEYSTORE_PATH="release/release.keystore"
if [ -f "$KEYSTORE_PATH" ]; then
    set_secret_from_file "ANDROID_KEYSTORE_BASE64" "$KEYSTORE_PATH"
    set_secret "ANDROID_KEYSTORE_PASSWORD" "aimanus2024"
    set_secret "ANDROID_KEY_ALIAS" "aimanus"
    set_secret "ANDROID_KEY_PASSWORD" "aimanus2024"
else
    echo -e "${YELLOW}⚠ Keystore not found at $KEYSTORE_PATH${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Setting up iOS secrets..."
echo "═══════════════════════════════════════════════════════════════"

# Apple credentials from environment or prompt
APPLE_TEAM_ID="${APPLE_TEAM_ID:-U549N38BV6}"
APPLE_KEY_ID="${APPLE_KEY_ID:-4A2M8S59A3}"
APPLE_ISSUER_ID="${APPLE_ISSUER_ID:-3812fee7-31e4-4330-ae7a-ca0a5992f475}"

set_secret "APPLE_TEAM_ID" "$APPLE_TEAM_ID"
set_secret "APPLE_KEY_ID" "$APPLE_KEY_ID"
set_secret "APPLE_ISSUER_ID" "$APPLE_ISSUER_ID"

if [ -n "$APPLE_PRIVATE_KEY" ]; then
    set_secret "APPLE_PRIVATE_KEY" "$APPLE_PRIVATE_KEY"
else
    echo -e "${YELLOW}⚠ APPLE_PRIVATE_KEY not set in environment${NC}"
    echo "Set it manually with: gh secret set APPLE_PRIVATE_KEY"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Setting up Google Play secrets..."
echo "═══════════════════════════════════════════════════════════════"

if [ -n "$GOOGLE_PLAY_KEY" ]; then
    # Create service account JSON
    SA_JSON=$(cat <<EOF
{
  "type": "service_account",
  "project_id": "megacursos",
  "private_key_id": "auto-generated",
  "private_key": "$GOOGLE_PLAY_KEY",
  "client_email": "full-owner@megacursos.iam.gserviceaccount.com",
  "client_id": "auto-generated",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
}
EOF
)
    echo "$SA_JSON" | base64 | gh secret set "GOOGLE_PLAY_SERVICE_ACCOUNT_JSON" --repo "$REPO"
    echo -e "${GREEN}✓ GOOGLE_PLAY_SERVICE_ACCOUNT_JSON set successfully${NC}"
else
    echo -e "${YELLOW}⚠ GOOGLE_PLAY_KEY not set in environment${NC}"
    echo "Set it manually with: gh secret set GOOGLE_PLAY_SERVICE_ACCOUNT_JSON"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""
gh secret list --repo "$REPO" 2>/dev/null || echo "Could not list secrets"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Verify all secrets are set: gh secret list"
echo "2. Create app in Google Play Console"
echo "3. Create app in App Store Connect"
echo "4. Trigger the workflows manually or push to main"
