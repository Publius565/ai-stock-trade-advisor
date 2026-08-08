import { createApp } from "./app";
import type { Env } from "./types";

const app = createApp();

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      return app.fetch(request, env, ctx);
    }
    // SPA assets — fall through to Pages/assets binding
    if (env.ASSETS) {
      return env.ASSETS.fetch(request);
    }
    return new Response("UI not built. Run: npm run build:web", { status: 503 });
  },
};
