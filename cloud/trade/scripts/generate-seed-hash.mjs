/**
 * Generate PBKDF2 password hash in the format used by the Worker auth module.
 * Usage: node scripts/generate-seed-hash.mjs [password] [saltBase64?]
 */
import { webcrypto } from "node:crypto";

const password = process.argv[2] ?? "password123";
const saltB64 = process.argv[3] ?? Buffer.from("seedlocaldevsalt").toString("base64");
const iterations = 100_000;

async function hashPassword(pw, saltBase64) {
  const enc = new TextEncoder();
  const salt = Buffer.from(saltBase64, "base64");
  const keyMaterial = await webcrypto.subtle.importKey(
    "raw",
    enc.encode(pw),
    "PBKDF2",
    false,
    ["deriveBits"],
  );
  const bits = await webcrypto.subtle.deriveBits(
    { name: "PBKDF2", salt, iterations, hash: "SHA-256" },
    keyMaterial,
    256,
  );
  const hashB64 = Buffer.from(bits).toString("base64");
  return `pbkdf2$${iterations}$${saltBase64}$${hashB64}`;
}

const out = await hashPassword(password, saltB64);
console.log(out);
