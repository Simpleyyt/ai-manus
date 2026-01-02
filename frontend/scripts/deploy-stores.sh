#!/bin/bash
# AI Manus - One-Click App Store Deployment
# Requires: Android SDK, Xcode (for iOS), store apps created

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           AI MANUS - APP STORE DEPLOYMENT                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"

cd "$(dirname "$0")/.."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BUNDLE_ID="com.aimanus.app"
APP_NAME="AI Manus"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js$(node -v)${NC}"

# Build web app
echo -e "\n${YELLOW}Building web app...${NC}"
npm run build
echo -e "${GREEN}✓ Web build complete${NC}"

# Sync Capacitor
echo -e "\n${YELLOW}Syncing Capacitor...${NC}"
npx cap sync
echo -e "${GREEN}✓ Capacitor synced${NC}"

# Check for Android SDK
if [ -n "$ANDROID_HOME" ] || [ -n "$ANDROID_SDK_ROOT" ]; then
    echo -e "\n${YELLOW}Building Android AAB...${NC}"
    cd android
    ./gradlew bundleRelease
    AAB_PATH="app/build/outputs/bundle/release/app-release.aab"
    if [ -f "$AAB_PATH" ]; then
        AAB_SHA=$(sha256sum "$AAB_PATH" | cut -d' ' -f1)
        echo -e "${GREEN}✓ AAB built: $AAB_PATH${NC}"
        echo -e "  SHA256: $AAB_SHA"
        cp "$AAB_PATH" "../release/"
    fi
    cd ..
else
    echo -e "${YELLOW}⚠ ANDROID_HOME not set - skipping Android build${NC}"
    echo "  Set ANDROID_HOME or use GitHub Actions for Android builds"
fi

# Check for Xcode (macOS only)
if [[ "$OSTYPE" == "darwin"* ]] && command -v xcodebuild &> /dev/null; then
    echo -e "\n${YELLOW}Building iOS IPA...${NC}"
    cd ios/App

    # Build archive
    xcodebuild -workspace App.xcworkspace \
        -scheme App \
        -configuration Release \
        -archivePath ./build/App.xcarchive \
        archive \
        CODE_SIGN_STYLE=Automatic

    # Export IPA
    xcodebuild -exportArchive \
        -archivePath ./build/App.xcarchive \
        -exportPath ./build \
        -exportOptionsPlist ExportOptions.plist

    if [ -f "./build/App.ipa" ]; then
        IPA_SHA=$(sha256sum "./build/App.ipa" | cut -d' ' -f1)
        echo -e "${GREEN}✓ IPA built: ./build/App.ipa${NC}"
        echo -e "  SHA256: $IPA_SHA"
        cp "./build/App.ipa" "../../release/"
    fi
    cd ../..
else
    echo -e "${YELLOW}⚠ Xcode not available - skipping iOS build${NC}"
    echo "  Use GitHub Actions macOS runner for iOS builds"
fi

# Upload to stores (if tools available)
if command -v fastlane &> /dev/null; then
    echo -e "\n${YELLOW}Uploading to stores via Fastlane...${NC}"

    # Android
    if [ -f "release/app-release.aab" ]; then
        echo "Uploading to Play Console..."
        # fastlane supply --aab release/app-release.aab --track internal
        echo -e "${GREEN}✓ Would upload to Play Console (uncomment fastlane command)${NC}"
    fi

    # iOS
    if [ -f "release/App.ipa" ]; then
        echo "Uploading to TestFlight..."
        # fastlane pilot upload --ipa release/App.ipa
        echo -e "${GREEN}✓ Would upload to TestFlight (uncomment fastlane command)${NC}"
    fi
fi

echo -e "\n══════════════════════════════════════════════════════════════"
echo -e "DEPLOYMENT COMPLETE"
echo -e "══════════════════════════════════════════════════════════════"
echo -e "Bundle ID: $BUNDLE_ID"
echo -e "App Name: $APP_NAME"
echo -e ""
echo -e "Artifacts in ./release/:"
ls -la release/ 2>/dev/null || echo "  (no artifacts yet)"
echo -e ""
echo -e "Next steps:"
echo -e "1. Upload AAB to Play Console: https://play.google.com/console"
echo -e "2. Upload IPA via Transporter or fastlane"
echo -e "══════════════════════════════════════════════════════════════"
