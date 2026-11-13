import { expect, test } from "vitest";
import { buildApp } from "../src/app.js";

test("health endpoint", async () => {
  const res = await buildApp().inject({ method: "GET", url: "/api/health" });
  expect(res.statusCode).toBe(200);
  expect(res.json().status).toBe("ok");
});
