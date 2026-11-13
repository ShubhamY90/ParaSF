import { apiFetch } from "./client";

// ─── Types ───────────────────────────────────────────────────────────────────

export interface FarmerProfileCreate {
  phone?: string;
  address?: string;
  district?: string;
  state?: string;
}

export interface FarmerProfileOut {
  id: number;
  user_id: number;
  phone: string | null;
  address: string | null;
  district: string | null;
  state: string | null;
  created_at: string;
}

export interface CropCreate {
  crop_type: string;
  season?: string;
  area_hectares?: number;
}

export interface CropOut {
  id: number;
  farm_id: number;
  crop_type: string;
  season: string | null;
  area_hectares: number | null;
}

export interface FarmCreate {
  name: string;
  area_hectares?: number;
  latitude?: number;
  longitude?: number;
}

export interface FarmOut {
  id: number;
  farmer_profile_id: number;
  name: string;
  area_hectares: number | null;
  latitude: number | null;
  longitude: number | null;
  boundary_geojson: string | null;
  created_at: string;
  crops: CropOut[];
}

export interface BankAccountCreate {
  account_holder_name: string;
  account_number: string;
  bank_name?: string;
  ifsc_code?: string;
}

export interface BankAccountOut {
  id: number;
  farmer_profile_id: number;
  account_holder_name: string;
  masked_account_number: string;
  bank_name: string | null;
  ifsc_code: string | null;
  verification_status: "pending" | "verified" | "failed";
  verified_at: string | null;
  created_at: string;
}

export interface PolicyCreate {
  policy_number: string;
  farm_id: number;
  farmer_profile_id: number;
  coverage_start: string;
  coverage_end: string;
  sum_insured: number;
  rainfall_trigger_mm?: number;
  rainfall_max_payout_mm?: number;
  flood_trigger_level?: number;
  payout_limit?: number;
  status?: string;
}

export interface PolicyUpdate {
  coverage_start?: string;
  coverage_end?: string;
  sum_insured?: number;
  rainfall_trigger_mm?: number;
  rainfall_max_payout_mm?: number;
  flood_trigger_level?: number;
  payout_limit?: number;
  status?: string;
}

export interface PolicyOut {
  id: number;
  policy_number: string;
  farm_id: number;
  farmer_profile_id: number;
  insurer_id: number;
  coverage_start: string;
  coverage_end: string;
  sum_insured: number;
  rainfall_trigger_mm: number | null;
  rainfall_max_payout_mm: number | null;
  flood_trigger_level: number | null;
  payout_limit: number | null;
  status: string;
  created_at: string;
}

export interface FarmerSummary {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  phone: string | null;
  district: string | null;
  state: string | null;
  farm_count: number;
  policy_count: number;
}

export interface FarmerDetail extends FarmerSummary {
  farms: FarmOut[];
  policies: PolicyOut[];
}

// ─── API functions ────────────────────────────────────────────────────────────

// Farmer profile
export async function getMyProfile(): Promise<FarmerProfileOut> {
  return apiFetch<FarmerProfileOut>("/farmers/profile");
}

export async function upsertMyProfile(data: FarmerProfileCreate): Promise<FarmerProfileOut> {
  return apiFetch<FarmerProfileOut>("/farmers/profile", { method: "POST", body: data });
}

// Farms
export async function getMyFarms(): Promise<FarmOut[]> {
  return apiFetch<FarmOut[]>("/farmers/farms");
}

export async function createFarm(data: FarmCreate): Promise<FarmOut> {
  return apiFetch<FarmOut>("/farmers/farms", { method: "POST", body: data });
}

export async function getFarm(id: number): Promise<FarmOut> {
  return apiFetch<FarmOut>(`/farmers/farms/${id}`);
}

export async function addCrop(farmId: number, data: CropCreate): Promise<CropOut> {
  return apiFetch<CropOut>(`/farmers/farms/${farmId}/crops`, { method: "POST", body: data });
}

// Bank account
export async function getBankAccount(): Promise<BankAccountOut> {
  return apiFetch<BankAccountOut>("/farmers/bank-account");
}

export async function submitBankAccount(data: BankAccountCreate): Promise<BankAccountOut> {
  return apiFetch<BankAccountOut>("/farmers/bank-account", { method: "POST", body: data });
}

// Policies (insurer)
export async function listPolicies(farmerId?: number): Promise<PolicyOut[]> {
  const qs = farmerId !== undefined ? `?farmer_id=${farmerId}` : "";
  return apiFetch<PolicyOut[]>(`/policies/${qs}`);
}

export async function createPolicy(data: PolicyCreate): Promise<PolicyOut> {
  return apiFetch<PolicyOut>("/policies/", { method: "POST", body: data });
}

export async function updatePolicy(id: number, data: PolicyUpdate): Promise<PolicyOut> {
  return apiFetch<PolicyOut>(`/policies/${id}`, { method: "PATCH", body: data });
}

// Admin / insurer farmer search
export async function searchFarmers(query?: string): Promise<FarmerSummary[]> {
  const qs = query ? `?search=${encodeURIComponent(query)}` : "";
  return apiFetch<FarmerSummary[]>(`/admin/farmers/${qs}`);
}

export async function getFarmerDetail(profileId: number): Promise<FarmerDetail> {
  return apiFetch<FarmerDetail>(`/admin/farmers/${profileId}`);
}
