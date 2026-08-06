import type { AuthUser, Env, MembershipPermissions } from "../types";
import { newId, randomToken, sha256Hex, verifyPassword } from "./crypto";

type UserRow = {
  id: string;
  email: string;
  password_hash: string;
  name: string | null;
  is_active: number;
};

type MembershipRow = {
  role: string;
  permissions_json: string;
  status: string;
};

/**
 * Thin adapter over Publiusly-compatible `users` + `app_memberships`.
 * At home, adjust column names here if production schema differs.
 */
export class UserRepository {
  constructor(
    private db: D1Database,
    private appId: string,
  ) {}

  async findByEmail(email: string): Promise<UserRow | null> {
    return (
      (await this.db
        .prepare(
          `SELECT id, email, password_hash, name, is_active
           FROM users WHERE email = ? COLLATE NOCASE LIMIT 1`,
        )
        .bind(email.trim())
        .first<UserRow>()) ?? null
    );
  }

  async getMembership(userId: string): Promise<MembershipRow | null> {
    return (
      (await this.db
        .prepare(
          `SELECT role, permissions_json, status
           FROM app_memberships
           WHERE user_id = ? AND app_id = ?
           LIMIT 1`,
        )
        .bind(userId, this.appId)
        .first<MembershipRow>()) ?? null
    );
  }
}

export class AuthService {
  private users: UserRepository;

  constructor(
    private env: Env,
    private cookieName = "trade_session",
  ) {
    this.users = new UserRepository(env.DB, env.APP_ID || "trade");
  }

  parsePermissions(json: string): MembershipPermissions {
    try {
      return JSON.parse(json) as MembershipPermissions;
    } catch {
      return {};
    }
  }

  async login(
    email: string,
    password: string,
  ): Promise<
    | { ok: true; user: AuthUser; token: string; maxAge: number }
    | { ok: false; status: 401 | 403; error: string }
  > {
    const user = await this.users.findByEmail(email);
    if (!user || !user.is_active) {
      return { ok: false, status: 401, error: "Invalid email or password" };
    }
    const valid = await verifyPassword(password, user.password_hash);
    if (!valid) {
      return { ok: false, status: 401, error: "Invalid email or password" };
    }

    const membership = await this.users.getMembership(user.id);
    if (!membership || membership.status !== "active") {
      return {
        ok: false,
        status: 403,
        error: "AppAccessDenied: no active trade membership",
      };
    }

    const token = randomToken();
    const tokenHash = await sha256Hex(token);
    const ttl = Number(this.env.SESSION_TTL_SECONDS || "604800");
    const expiresAt = Math.floor(Date.now() / 1000) + ttl;
    const sessionId = newId("sess");

    await this.env.DB.prepare(
      `INSERT INTO sessions (id, user_id, token_hash, expires_at, created_at)
       VALUES (?, ?, ?, ?, unixepoch())`,
    )
      .bind(sessionId, user.id, tokenHash, expiresAt)
      .run();

    return {
      ok: true,
      token,
      maxAge: ttl,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: membership.role,
        permissions: this.parsePermissions(membership.permissions_json),
      },
    };
  }

  async logout(token: string | undefined): Promise<void> {
    if (!token) return;
    const tokenHash = await sha256Hex(token);
    await this.env.DB.prepare(`DELETE FROM sessions WHERE token_hash = ?`)
      .bind(tokenHash)
      .run();
  }

  async resolveSession(token: string | undefined): Promise<AuthUser | null> {
    if (!token) return null;
    const tokenHash = await sha256Hex(token);
    const now = Math.floor(Date.now() / 1000);
    const row = await this.env.DB.prepare(
      `SELECT u.id, u.email, u.name, m.role, m.permissions_json, m.status, s.expires_at
       FROM sessions s
       JOIN users u ON u.id = s.user_id
       JOIN app_memberships m ON m.user_id = u.id AND m.app_id = ?
       WHERE s.token_hash = ? AND u.is_active = 1
       LIMIT 1`,
    )
      .bind(this.env.APP_ID || "trade", tokenHash)
      .first<{
        id: string;
        email: string;
        name: string | null;
        role: string;
        permissions_json: string;
        status: string;
        expires_at: number;
      }>();

    if (!row || row.status !== "active" || row.expires_at < now) {
      if (row) {
        await this.env.DB.prepare(`DELETE FROM sessions WHERE token_hash = ?`)
          .bind(tokenHash)
          .run();
      }
      return null;
    }

    return {
      id: row.id,
      email: row.email,
      name: row.name,
      role: row.role,
      permissions: this.parsePermissions(row.permissions_json),
    };
  }

  cookieHeader(token: string, maxAge: number): string {
    const parts = [
      `${this.cookieName}=${token}`,
      "Path=/",
      "HttpOnly",
      "Secure",
      "SameSite=Lax",
      `Max-Age=${maxAge}`,
    ];
    return parts.join("; ");
  }

  clearCookieHeader(): string {
    return `${this.cookieName}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`;
  }

  readCookie(header: string | null): string | undefined {
    if (!header) return undefined;
    const parts = header.split(";").map((p) => p.trim());
    for (const part of parts) {
      const eq = part.indexOf("=");
      if (eq === -1) continue;
      const name = part.slice(0, eq);
      if (name === this.cookieName) return part.slice(eq + 1);
    }
    return undefined;
  }
}

export function requirePermission(
  user: AuthUser,
  key: keyof MembershipPermissions,
): boolean {
  return Boolean(user.permissions[key]);
}
