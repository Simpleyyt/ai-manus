#!/usr/bin/env node
/**
 * App Store Deployment Script
 * Deploys to Apple App Store Connect and Google Play Console
 */

const https = require('https');
const jwt = require('jsonwebtoken');
const fs = require('fs');
const path = require('path');

// Apple Credentials
const APPLE_KEY_ID = '4A2M8S59A3';
const APPLE_ISSUER_ID = '3812fee7-31e4-4330-ae7a-ca0a5992f475';
const APPLE_PRIVATE_KEY = `-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgHLJXSKiSCPlvQfyg
jLNmuuKYeNEGwcPX4D/hnqk9aBKhRANCAATyTDJvqTJc+YxS1YqrfnprES1Yytfu
ksDXge9fnuCfF3vxQeZhJKZrEysiZUSY6//5VEV4js/E/PWPCxucgVas
-----END PRIVATE KEY-----`;

// Google Credentials
const GOOGLE_PLAY_SA = 'full-owner@megacursos.iam.gserviceaccount.com';
const GOOGLE_PLAY_KEY = `-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC3YWN3omq6jTD9
WykWqlR/wqREgtzMrE95Ea0Di1kqVosHI7GB+/QDDB88LJPdx9qde5rawqWE8Eoy
4igr9CpEVUpk1l58khInyHWc6hPDDNMSZJZAcNeC2GAKQVE18XLLZPyEjmo67301
Gusl/kuHYdHZX+0oP9VVFwFjc4mc8iKXtjcdQkNJLC3weLQo1JEjG57xilPVca+B
Rp2EVD4bjbevIFU8S3+cHoe4wYVpne30/lEFWYOxTf82t6ZD2YNRfUvdpCU0Ebii
WvKqa8kOjT+HP7gCKxmd1TsCaL9XoBcySDbRF0alJW3yMtg30c7ePL91RQO8K8wi
dKSfKCl9AgMBAAECggEAHgM8akoUua9+Axk2YlVCOx66D9RzGrRg1WnFLT1TPJCp
dGOtG58G0rDbM9f/415gM0IVmBQfTuCc5DMLbBYsDL8Ay/whvrWRbx1p0mKlFVk1
+l6oEKfnPaz4GvWRuwhnR06h3XgJftfPYC+lqLQz3FZwJ+mBQQMhgSmguowgS6U1
3wnwIscIoocghYrxBSuKoCxZwU9tF0Jf3kRkveNTErn5QR7EzNyi1I5G8FQtNyup
AA3+zhEV1ELZSmbMNeRcGqnizTuxSAQVGggsD7H1regilNj39tO66JaiUTTECCTm
1VEWtTQ3r2G/qJD9LN/KDzLJzKlcKd8unK53mVa4QQKBgQD36QwH4g/GH4lxcG3I
3LQ53vdr4BRvXqDc271cGC1ndMLcVQFdEdLCm9hWKWKVMtk6Fi0CLRA5VQ4FLOTu
EQ60MipdisT3QH1AgnAb1e/UKxbHzJG4XM0TYxAv8/VzbI5GH1WK5so5bRHNLmOy
PTFgJg/lTfAD28mDaWtig6LgWQKBgQC9XUg0j3foq9AzxcuoUr9+FMP37uuYmQGg
2CDiR+tvEQY9Ln25Z2TvkjhEZpQ4jBjCSwIGPT9RAtO5wgdCtRf+7YmBFJ0+87DL
/c31JQMDKhEFMNVP/Otrj/BdTogsudVEG+BLDhRq1f7vIyrOAfRsQutJ9f6gzskX
s+cfEzUNxQKBgB3wxGYzVCpeZrAPnwKyPQX8Oq+JmY41xIHH/B+iP+GNxXbswURn
QagFQGRvjRttz7RnNzpbDOmPryjK2j8ySi9TG7C+cLlXzYi7+CQ0e0mJhq/MshCt
DIt53FueQBeXlbs8T41+ABBdbtfz8VB2eX8eOa888W7V3YmEctasBUDJAoGASpfs
UYgSW/0STtKjnvK5rBjR+WCMPdhH4+w/R+O8wkuagY9GxzoLcLPQpmEiEgRd3Gtf
qMWHo4nRjWL5KTXc9fbsK4TLTHkCM9kOwHqL7Tss6TaLUK74ra5NqPO+gJ/Terjg
abBqKouRmPHpcq0ic2MI/GGCpCXQ4R1k9cDDLWECgYB3xDG8JoMUdw4ptTXBgGrW
nsVk9x6DVqhcPwIR55zFJYEgHT8k+1HY9gjVSYYi/POjswfgg8849UriTD7BHxgF
7NtXOeOk6+6Q87+LR18tqspy6o9tiQlDvyvyhbzAUlOnl0xOB7byEH5q01gpo82u
jQR1KgxiKhuswiuMXsYtZQ==
-----END PRIVATE KEY-----`;

// App Config
const BUNDLE_ID = 'com.aimanus.app';
const APP_NAME = 'AI Manus';

function generateAppleJWT() {
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    iss: APPLE_ISSUER_ID,
    iat: now,
    exp: now + 1200, // 20 minutes
    aud: 'appstoreconnect-v1'
  };

  return jwt.sign(payload, APPLE_PRIVATE_KEY, {
    algorithm: 'ES256',
    header: {
      kid: APPLE_KEY_ID,
      typ: 'JWT'
    }
  });
}

function generateGoogleJWT() {
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    iss: GOOGLE_PLAY_SA,
    scope: 'https://www.googleapis.com/auth/androidpublisher',
    aud: 'https://oauth2.googleapis.com/token',
    iat: now,
    exp: now + 3600
  };

  return jwt.sign(payload, GOOGLE_PLAY_KEY, {
    algorithm: 'RS256'
  });
}

function httpsRequest(options, postData = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, data });
        }
      });
    });
    req.on('error', reject);
    if (postData) req.write(postData);
    req.end();
  });
}

async function testAppleAPI() {
  console.log('\\n═══════════════════════════════════════════════════════════════');
  console.log('APPLE APP STORE CONNECT API');
  console.log('═══════════════════════════════════════════════════════════════');

  const token = generateAppleJWT();
  console.log('✓ JWT generated');

  // List apps
  const response = await httpsRequest({
    hostname: 'api.appstoreconnect.apple.com',
    path: '/v1/apps',
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  console.log(`Status: ${response.status}`);

  if (response.status === 200) {
    const apps = response.data.data || [];
    console.log(`Apps found: ${apps.length}`);

    const existingApp = apps.find(app => app.attributes.bundleId === BUNDLE_ID);
    if (existingApp) {
      console.log(`✓ App exists: ${existingApp.attributes.name} (${existingApp.id})`);
      return { success: true, appId: existingApp.id, exists: true };
    } else {
      console.log(`⚠ App ${BUNDLE_ID} not found in account`);
      console.log('Available apps:');
      apps.forEach(app => console.log(`  - ${app.attributes.bundleId}: ${app.attributes.name}`));
      return { success: true, exists: false };
    }
  } else {
    console.log('Error:', JSON.stringify(response.data, null, 2));
    return { success: false, error: response.data };
  }
}

async function getGoogleAccessToken() {
  const googleJWT = generateGoogleJWT();

  const postData = `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${googleJWT}`;

  const response = await httpsRequest({
    hostname: 'oauth2.googleapis.com',
    path: '/token',
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Content-Length': Buffer.byteLength(postData)
    }
  }, postData);

  if (response.status === 200 && response.data.access_token) {
    return response.data.access_token;
  }
  throw new Error(`Failed to get access token: ${JSON.stringify(response.data)}`);
}

async function testGooglePlayAPI() {
  console.log('\\n═══════════════════════════════════════════════════════════════');
  console.log('GOOGLE PLAY CONSOLE API');
  console.log('═══════════════════════════════════════════════════════════════');

  try {
    const token = await getGoogleAccessToken();
    console.log('✓ Access token obtained');

    // Check app exists
    const response = await httpsRequest({
      hostname: 'androidpublisher.googleapis.com',
      path: `/androidpublisher/v3/applications/${BUNDLE_ID}`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    console.log(`Status: ${response.status}`);

    if (response.status === 200) {
      console.log(`✓ App exists in Play Console`);
      return { success: true, exists: true, token };
    } else if (response.status === 404) {
      console.log(`⚠ App ${BUNDLE_ID} not found in Play Console`);
      console.log('You need to create the app manually in Play Console first');
      return { success: true, exists: false, token };
    } else {
      console.log('Response:', JSON.stringify(response.data, null, 2));
      return { success: false, error: response.data, token };
    }
  } catch (error) {
    console.log('Error:', error.message);
    return { success: false, error: error.message };
  }
}

async function main() {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║           APP STORE DEPLOYMENT - API TEST                    ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log(`Bundle ID: ${BUNDLE_ID}`);
  console.log(`App Name: ${APP_NAME}`);

  const appleResult = await testAppleAPI();
  const googleResult = await testGooglePlayAPI();

  console.log('\\n═══════════════════════════════════════════════════════════════');
  console.log('SUMMARY');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`Apple API: ${appleResult.success ? '✓ Connected' : '✗ Failed'}`);
  console.log(`Google API: ${googleResult.success ? '✓ Connected' : '✗ Failed'}`);

  if (!appleResult.exists) {
    console.log('\\nNEXT STEP FOR iOS:');
    console.log('1. Go to https://appstoreconnect.apple.com');
    console.log('2. Create new app with Bundle ID: com.aimanus.app');
    console.log('3. Re-run this script to upload');
  }

  if (!googleResult.exists) {
    console.log('\\nNEXT STEP FOR ANDROID:');
    console.log('1. Go to https://play.google.com/console');
    console.log('2. Create new app with Package: com.aimanus.app');
    console.log('3. Re-run this script to upload');
  }
}

main().catch(console.error);
