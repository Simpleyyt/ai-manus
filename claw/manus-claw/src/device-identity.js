import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { homedir } from 'node:os';

const DEFAULT_IDENTITY_PATH = path.join(homedir(), '.openclaw', 'plugins', 'manus-claw', 'device.json');
const ED25519_SPKI_PREFIX = Buffer.from('302a300506032b6570032100', 'hex');

function base64UrlEncode(buf) {
  return buf.toString('base64').replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/g, '');
}

function derivePublicKeyRaw(pem) {
  const der = crypto.createPublicKey(pem).export({ type: 'spki', format: 'der' });
  if (der.length === ED25519_SPKI_PREFIX.length + 32 &&
      der.subarray(0, ED25519_SPKI_PREFIX.length).equals(ED25519_SPKI_PREFIX)) {
    return der.subarray(ED25519_SPKI_PREFIX.length);
  }
  return der;
}

function fingerprintPublicKey(pem) {
  return crypto.createHash('sha256').update(derivePublicKeyRaw(pem)).digest('hex');
}

function generateIdentity() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
  const pub = publicKey.export({ type: 'spki', format: 'pem' }).toString();
  const priv = privateKey.export({ type: 'pkcs8', format: 'pem' }).toString();
  return { deviceId: fingerprintPublicKey(pub), publicKeyPem: pub, privateKeyPem: priv };
}

export function loadOrCreateDeviceIdentity(identityPath = DEFAULT_IDENTITY_PATH) {
  try {
    if (fs.existsSync(identityPath)) {
      const data = JSON.parse(fs.readFileSync(identityPath, 'utf8'));
      if (data?.version === 1 && data.deviceId && data.publicKeyPem && data.privateKeyPem) {
        return { deviceId: data.deviceId, publicKeyPem: data.publicKeyPem, privateKeyPem: data.privateKeyPem };
      }
    }
  } catch { /* regenerate */ }

  const identity = generateIdentity();
  fs.mkdirSync(path.dirname(identityPath), { recursive: true });
  fs.writeFileSync(identityPath, JSON.stringify({
    version: 1, ...identity, createdAtMs: Date.now(),
  }, null, 2) + '\n', { mode: 0o600 });
  return identity;
}

export function buildDeviceAuthField({ identity, clientId, clientMode, role, scopes, token, nonce }) {
  const signedAtMs = Date.now();
  const version = nonce ? 'v2' : 'v1';
  const parts = [version, identity.deviceId, clientId, clientMode, role, scopes.join(','), String(signedAtMs), token ?? ''];
  if (version === 'v2') parts.push(nonce ?? '');
  const payload = parts.join('|');

  const privKey = crypto.createPrivateKey(identity.privateKeyPem);
  const signature = base64UrlEncode(crypto.sign(null, Buffer.from(payload, 'utf8'), privKey));
  const publicKey = base64UrlEncode(derivePublicKeyRaw(identity.publicKeyPem));

  const result = { id: identity.deviceId, publicKey, signature, signedAt: signedAtMs };
  if (nonce) result.nonce = nonce;
  return result;
}
