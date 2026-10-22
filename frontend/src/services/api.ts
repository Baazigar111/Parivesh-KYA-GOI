/**
 * api.ts
 * ------
 * Client service to interface with FastAPI backend (Render, Cloud Run, ECS, or local dev).
 */

import {
  MasterActivity,
  MasterSubActivity,
  ClearanceRequestPayload,
  ClearanceResponse,
} from "../types/clearance";
import defaultActivities from "../data/activities.json";
import defaultSubactivities from "../data/subactivities.json";

function cleanApiBase(url?: string): string {
  if (!url) return "http://127.0.0.1:8000";
  let cleaned = url.trim();
  // Strip trailing slashes
  cleaned = cleaned.replace(/\/+$/, "");
  // If the user appended /api/v1 or /api to NEXT_PUBLIC_API_URL, strip it so we don't double up
  cleaned = cleaned.replace(/\/api\/v1$/, "");
  cleaned = cleaned.replace(/\/api$/, "");
  return cleaned;
}

// Accepts API_URL or NEXT_PUBLIC_API_URL
const API_BASE_URL = cleanApiBase(process.env.API_URL || process.env.NEXT_PUBLIC_API_URL);

export async function fetchMasterActivities(): Promise<MasterActivity[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/activities`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "default",
    });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data;
      }
    }
  } catch (err) {
    console.warn("FastAPI activities request failed, using complete 56-sector catalog:", err);
  }
  return defaultActivities;
}

export async function fetchSubActivities(
  activityId: number
): Promise<MasterSubActivity[]> {
  const localCatalog = (defaultSubactivities as Record<string, MasterSubActivity[]>)[String(activityId)];

  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/subactivities?activity_id=${activityId}`,
      {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }
    );
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data;
      }
    }
  } catch (err) {
    console.warn(`Sub-activities request failed for activity ${activityId}, using cached catalog:`, err);
  }

  if (localCatalog && localCatalog.length > 0) {
    return localCatalog;
  }

  return [{ id: 0, name: "General / All Categories" }];
}

export async function evaluateClearances(
  payload: ClearanceRequestPayload
): Promise<ClearanceResponse> {
  const endpoints = [
    `${API_BASE_URL}/api/v1/clearances`,
    `${API_BASE_URL}/api/clearances`,
  ];

  let lastRes: Response | null = null;
  let lastErrorText = "";

  for (const url of endpoints) {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        return await res.json();
      }

      lastRes = res;
      lastErrorText = await res.text();
      // If not a 404, break out and show the actual error
      if (res.status !== 404) {
        break;
      }
    } catch (err: any) {
      lastErrorText = err.message || String(err);
    }
  }

  throw new Error(
    `Evaluation failed (HTTP ${lastRes?.status || "ERR"}): ${lastErrorText || lastRes?.statusText || "Could not reach backend service"}`
  );
}

export async function checkBackendHealth(): Promise<{
  status: string;
  cache_driver?: string;
  version?: string;
}> {
  const healthEndpoints = [
    `${API_BASE_URL}/api/v1/health`,
    `${API_BASE_URL}/api/health`,
    `${API_BASE_URL}/health`,
    `${API_BASE_URL}/`
  ];

  for (const url of healthEndpoints) {
    try {
      const res = await fetch(url, { method: "GET" });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // try next health endpoint
    }
  }
  return { status: "disconnected" };
}
