/**
 * Shared demo-account role mapping.
 * Single source of truth — imported by auth.ts and AuthContext.tsx.
 */
import type { UserRole } from "../api/auth";

export const DEMO_ROLES: Record<string, UserRole> = {
  "farmer@paratrust.dev": "farmer",
  "insurer@paratrust.dev": "insurer",
  "auditor@paratrust.dev": "auditor",
  "admin@paratrust.dev": "admin",
};
