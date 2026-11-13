import { apiFetch } from "./client";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface GeoFeature {
  type: "Feature";
  geometry: GeoJSON.Geometry;
  properties: Record<string, unknown>;
}

export interface FeatureCollection {
  type: "FeatureCollection";
  features: GeoFeature[];
}

export interface DistrictProperties {
  id: string;
  name: string;
  centre: [number, number];  // [lat, lng]
  bbox: [number, number, number, number]; // [min_lng, min_lat, max_lng, max_lat]
  simulated: true;
  note: string;
}

export interface SensorProperties {
  id: string;
  name: string;
  sensor_type: "rainfall" | "water_level";
  status: "normal" | "faulty" | "offline";
  simulated: true;
  trust_score: number | null;
}

export interface WaterProperties {
  id: string;
  name: string;
  kind: "river" | "water_body";
  simulated: true;
}

export interface FarmProperties {
  farm_id: number;
  name: string;
  area_hectares: number | null;
  farmer_label: string;
  primary_crop: string | null;
  policy_status: string;
  sum_insured: number | null;
  is_own: boolean;
  in_demo_district: boolean;
  simulated: false;
  estimated_rainfall_mm: number | null;
  risk_category: string | null;
  claim_status: string | null;
}

export interface CropBrief {
  crop_type: string;
  season: string | null;
  area_hectares: number | null;
}

export interface PolicyBrief {
  id: number;
  policy_number: string;
  status: string;
  sum_insured: number;
  coverage_start: string;
  coverage_end: string;
}

export interface FarmMapDetail {
  farm_id: number;
  name: string;
  area_hectares: number | null;
  latitude: number | null;
  longitude: number | null;
  farmer_label: string;
  district: string | null;
  state: string | null;
  crops: CropBrief[];
  primary_crop: string | null;
  policy: PolicyBrief | null;
  policy_status: string;
  sum_insured: number | null;
  estimated_rainfall_mm: number | null;
  risk_category: string | null;
  claim_status: string | null;
  stage_notes: string[];
  in_demo_district: boolean;
}

// ─── API functions ────────────────────────────────────────────────────────────

export async function getDistrict(): Promise<GeoFeature> {
  return apiFetch<GeoFeature>("/geo/district");
}

export async function getSensors(): Promise<FeatureCollection> {
  return apiFetch<FeatureCollection>("/geo/sensors");
}

export async function getWater(): Promise<FeatureCollection> {
  return apiFetch<FeatureCollection>("/geo/water");
}

export async function getFarmsGeo(): Promise<FeatureCollection> {
  return apiFetch<FeatureCollection>("/geo/farms");
}

export async function getFarmDetail(farmId: number): Promise<FarmMapDetail> {
  return apiFetch<FarmMapDetail>(`/geo/farms/${farmId}`);
}
