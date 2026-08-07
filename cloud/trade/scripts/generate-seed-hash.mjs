/**
 * Generate Publiusly PBKDF2 password hash (iterationsHex:saltHex:hashHex).
 * Usage: node scripts/generate-seed-hash.mjs [password] [saltHex?]
 */
import { webcrypto } from "node:crypto";

const password = process.argv[2] ?? "password123";
const saltHex =
  process.argv[3] ??
  Buffer.from("seedlocaldevsalt").toString("hex"); // 16 bytes → 32 hex chars
const iterations = 100_000;

async function hashPassword(pw, saltHexStr) {
  const enc = new TextEncoder();
  const salt = Buffer.from(saltHexStr, "hex");
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
  const hashHex = Buffer.from(bits).toString("hex");
  return `${iterations.toString(16)}:${saltHexStr}:${hashHex}`;
}

const out = await hashPassword(password, saltHex);
console.log(out);
