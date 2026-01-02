# App Store Deployment Guide

## Overview

This project is configured for deployment to both Google Play Store and Apple App Store using Capacitor and GitHub Actions.

## Project Configuration

- **Bundle ID**: `com.aimanus.app`
- **App Name**: AI Manus
- **Version**: 1.0.0

## Prerequisites

### Google Play Store

1. Create a Google Play Developer account
2. Create a new app in Google Play Console
3. Create a Service Account with API access
4. Download the JSON key file

### Apple App Store

1. Apple Developer Program membership
2. Create App ID in Apple Developer Portal
3. Create provisioning profiles (Development & Distribution)
4. Generate App Store Connect API key

## GitHub Secrets Required

### Android Deployment

| Secret | Description |
|--------|-------------|
| `ANDROID_KEYSTORE_BASE64` | Base64 encoded keystore file |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_ALIAS` | Key alias (aimanus) |
| `ANDROID_KEY_PASSWORD` | Key password |
| `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` | Base64 encoded service account JSON |

### iOS Deployment

| Secret | Description |
|--------|-------------|
| `APPLE_TEAM_ID` | Apple Team ID (U549N38BV6) |
| `APPLE_KEY_ID` | App Store Connect API Key ID |
| `APPLE_ISSUER_ID` | App Store Connect Issuer ID |
| `APPLE_PRIVATE_KEY` | App Store Connect API Private Key |
| `APPLE_CERTIFICATE_P12` | Base64 encoded distribution certificate |
| `APPLE_CERTIFICATE_PASSWORD` | Certificate password |
| `APPLE_PROVISIONING_PROFILE` | Base64 encoded provisioning profile |

## Setting Up Secrets

### Encode Keystore for Android

```bash
base64 -i release/release.keystore | pbcopy
# or on Linux:
base64 release/release.keystore | xclip -selection clipboard
```

### Current Keystore Info

- **Location**: `frontend/release/release.keystore`
- **Alias**: `aimanus`
- **SHA256 Fingerprint**: `A2:CE:D2:87:6D:20:5F:26:58:79:D8:08:6D:ED:50:91:0D:A2:BC:11:B7:63:B7:92:8F:33:86:A3:5A:37:81:77`

## Digital Asset Links

For Android App Links verification, deploy the following file to your web server:

**Location**: `/.well-known/assetlinks.json`

```json
[
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "com.aimanus.app",
      "sha256_cert_fingerprints": [
        "A2:CE:D2:87:6D:20:5F:26:58:79:D8:08:6D:ED:50:91:0D:A2:BC:11:B7:63:B7:92:8F:33:86:A3:5A:37:81:77"
      ]
    }
  }
]
```

## Build Commands

### Local Development

```bash
# Build web app and sync to platforms
npm run cap:sync

# Open Android Studio
npm run cap:android

# Open Xcode
npm run cap:ios

# Build release APK
npm run build:android

# Build release AAB (for Play Store)
npm run build:android:bundle
```

### CI/CD

Workflows are triggered automatically on push to `main` branch or can be triggered manually:

- **Android**: `.github/workflows/android-deploy.yml`
- **iOS**: `.github/workflows/ios-deploy.yml`

## Store Listing Requirements

### Screenshots Needed

- Phone (1080x1920 or 1242x2208)
- 7" Tablet (optional)
- 10" Tablet (optional)

### Required Metadata

- Short description (80 chars max)
- Full description (4000 chars max)
- Privacy policy URL
- Support email

## Privacy Policy

Ensure you have a privacy policy URL. The policy should cover:
- Data collection practices
- Third-party services used
- User rights and data deletion

## Troubleshooting

### Android Build Fails

```bash
cd frontend/android
./gradlew clean
./gradlew bundleRelease --stacktrace
```

### iOS Build Fails

```bash
cd frontend/ios/App
pod deintegrate
pod install
```

### Signing Issues

- Verify keystore password
- Check provisioning profile expiration
- Regenerate certificates if expired
