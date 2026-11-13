import { buildApp } from "./app.js";
import { config } from "./core/config.js";

buildApp().listen({ port: config.port, host: "0.0.0.0" }).then(() => {
  console.log(`ParaTrust API on http://localhost:${config.port}`);
});
