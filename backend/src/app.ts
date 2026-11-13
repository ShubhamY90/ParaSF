import Fastify from "fastify";
import cors from "@fastify/cors";
import { config } from "./core/config.js";

export function buildApp() {
  const app = Fastify({ logger: false });
  app.register(cors, { origin: config.corsOrigins, credentials: true });

  app.get("/api/health", async () => ({ status: "ok", service: "paratrust-api" }));

  return app;
}
