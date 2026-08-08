const enc = new TextEncoder();

const PBKDF2_ITERATIONS = 100_000;
const PBKDF2_KEY_LENGTH = 256; // bits
const SALT_LENGTH = 16;

function toB64(buf: ArrayBuffer | Uint8Array): string {
  const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s);
}

function uint8ArrayToHex(arr: Uint8Array): string {
  return Array.from(arr)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function hexToUint8Array(hex: string): Uint8Array {
  const matches = hex.match(/.{1,2}/g);
  if (!matches) {
    throw new Error("Invalid hex string");
  }
  return new Uint8Array(matches.map((byte) => Number.parseInt(byte, 16)));
}

function timingSafeEqualBytes(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i]! ^ b[i]!;
  return diff === 0;
}

/**
 * Hash a password using PBKDF2-SHA256 (Publiusly production format).
 * Format: iterationsHex:saltHex:hashHex
 */
export async function hashPassword(
  password: string,
  iterations = PBKDF2_ITERATIONS,
  salt?: Uint8Array,
): Promise<string> {
  const usedSalt = salt ?? crypto.getRandomValues(new Uint8Array(SALT_LENGTH));
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    "PBKDF2",
    false,
    ["deriveBits"],
  );
  const saltBuffer = usedSalt.buffer.slice(
    usedSalt.byteOffset,
    usedSalt.byteOffset + usedSalt.byteLength,
  ) as ArrayBuffer;
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt: saltBuffer, iterations, hash: "SHA-256" },
    keyMaterial,
    PBKDF2_KEY_LENGTH,
  );
  return `${iterations.toString(16)}:${uint8ArrayToHex(usedSalt)}:${uint8ArrayToHex(new Uint8Array(bits))}`;
}

/** Verify against Publiusly `iterationsHex:saltHex:hashHex` hashes. */
export async function verifyPassword(
  password: string,
  stored: string,
): Promise<boolean> {
  try {
    const [iterationsHex, saltHex, hashHex] = stored.split(":");
    if (!iterationsHex || !saltHex || !hashHex) return false;

    const iterations = Number.parseInt(iterationsHex, 16);
    if (!Number.isFinite(iterations) || iterations <= 0) return false;

    const salt = hexToUint8Array(saltHex);
    const expectedHash = hexToUint8Array(hashHex);

    const keyMaterial = await crypto.subtle.importKey(
      "raw",
      enc.encode(password),
      "PBKDF2",
      false,
      ["deriveBits"],
    );
    const saltBuffer = salt.buffer.slice(
      salt.byteOffset,
      salt.byteOffset + salt.byteLength,
    ) as ArrayBuffer;
    const derived = await crypto.subtle.deriveBits(
      { name: "PBKDF2", salt: saltBuffer, iterations, hash: "SHA-256" },
      keyMaterial,
      PBKDF2_KEY_LENGTH,
    );
    return timingSafeEqualBytes(new Uint8Array(derived), expectedHash);
  } catch {
    return false;
  }
}

export async function sha256Hex(input: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", enc.encode(input));
  return [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export function randomToken(bytes = 32): string {
  const arr = crypto.getRandomValues(new Uint8Array(bytes));
  return toB64(arr).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function newId(prefix: string): string {
  return `${prefix}_${crypto.randomUUID().replace(/-/g, "")}`;
}
