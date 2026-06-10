import { getStore } from '@netlify/blobs';

const BLOB_STORE = 'pet-sitters-calendar';
const DATA_KEY = 'store';
const PIN_HASH_KEY = 'pin-hash';
// Must match storeWriteKey in config.js
const WRITE_KEY = 'psc-live-sync-7k9m2xq';

const DEFAULT_STORE = {
  version: 1,
  enquiries: [],
  bookings: [],
  availability: {},
};

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
      ...CORS,
    },
  });
}

async function hashPin(pin) {
  const data = new TextEncoder().encode(pin);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');
}

async function isAuthorized(blobStore, body) {
  if (body.writeKey === WRITE_KEY) return true;

  const pin = String(body.pin || '');
  if (pin.length < 4) return false;

  const storedHash = await blobStore.get(PIN_HASH_KEY);
  if (!storedHash) {
    await blobStore.set(PIN_HASH_KEY, await hashPin(pin));
    return true;
  }

  return storedHash === await hashPin(pin);
}

export default async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: CORS });
  }

  const blobStore = getStore(BLOB_STORE);

  if (req.method === 'GET') {
    const data = await blobStore.get(DATA_KEY, { type: 'json' });
    return json(data || DEFAULT_STORE);
  }

  if (req.method === 'POST') {
    let body;
    try {
      body = await req.json();
    } catch {
      return json({ error: 'Invalid JSON' }, 400);
    }

    if (!body.store || typeof body.store !== 'object') {
      return json({ error: 'Missing store' }, 400);
    }

    if (!(await isAuthorized(blobStore, body))) {
      return json({ error: 'Unauthorized' }, 401);
    }

    await blobStore.set(DATA_KEY, JSON.stringify(body.store));
    return json({ ok: true, updatedAt: new Date().toISOString() });
  }

  return json({ error: 'Method not allowed' }, 405);
};
