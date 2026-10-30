// Web Crypto side of the question bank (see specs/mock-tests.md section 5; the Python side is scripts/bank/bankcrypto.py).
// key = PBKDF2-SHA256(password, salt, iter) -> AES-256-GCM. File = "HSKB" + 12-byte IV + ciphertext.
const MAGIC = [0x48, 0x53, 0x4b, 0x42];
const CHECK = "hsk-bank-ok";
const DB_NAME = "hskfc-bank";
const STORE = "keys";

const subtle = () => globalThis.crypto && globalThis.crypto.subtle;

export function b64ToBytes(b64) {
  const s = String(b64).replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(s + "=".repeat((4 - (s.length % 4)) % 4));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

/** meta.json: null when there is no bank (404), "error" when it could not be fetched (offline and not cached). */
export async function fetchMeta() {
  try {
    const res = await fetch("bank/meta.json", { cache: "no-cache" });
    if (res.status === 404) return null;
    if (!res.ok) return "error";
    const meta = await res.json();
    return meta && meta.salt && meta.check ? meta : null;
  } catch (e) {
    return "error";
  }
}

export async function keyFromPassword(password, meta) {
  const base = await subtle().importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveKey"]);
  return subtle().deriveKey(
    { name: "PBKDF2", salt: b64ToBytes(meta.salt), iterations: meta.iter, hash: "SHA-256" },
    base, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
}

export function keyFromRaw(b64url) {
  const raw = b64ToBytes(b64url);
  if (raw.length !== 32) throw new Error("bad key length");
  return subtle().importKey("raw", raw, { name: "AES-GCM" }, false, ["decrypt"]);
}

export async function decryptBlob(key, buffer) {
  const bytes = new Uint8Array(buffer);
  if (bytes.length < 32 || MAGIC.some((b, i) => bytes[i] !== b)) throw new Error("not an encrypted file");
  return subtle().decrypt({ name: "AES-GCM", iv: bytes.slice(4, 16) }, key, bytes.slice(16));
}

export async function keyMatches(key, meta) {
  try {
    const plain = await decryptBlob(key, b64ToBytes(meta.check));
    return new TextDecoder().decode(plain) === CHECK;
  } catch (e) {
    return false;
  }
}

// ---- the key is kept as a (non-extractable) CryptoKey in IndexedDB; if that fails it only lives in memory ----
function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function withStore(mode, fn) {
  const db = await openDb();
  try {
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, mode);
      const req = fn(tx.objectStore(STORE));
      tx.oncomplete = () => resolve(req ? req.result : undefined);
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally {
    db.close();
  }
}

export async function loadStoredKey() {
  try { return (await withStore("readonly", (s) => s.get("key"))) || null; } catch (e) { return null; }
}

export async function storeKey(key) {
  try { await withStore("readwrite", (s) => s.put(key, "key")); return true; } catch (e) { return false; }
}

export async function clearStoredKey() {
  try { await withStore("readwrite", (s) => s.delete("key")); } catch (e) { /* nothing stored */ }
}
