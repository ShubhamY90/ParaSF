import "dotenv/config";

export const config = {
  port: Number(process.env.PORT ?? 8000),
  jwtSecret: process.env.JWT_SECRET ?? "change-me-in-dev-only",
  corsOrigins: ["http://localhost:5173"],
  simulationSeed: Number(process.env.SIMULATION_SEED ?? 42),
};
