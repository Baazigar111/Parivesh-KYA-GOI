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

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function fetchMasterActivities(): Promise<MasterActivity[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/activities`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      cache: "default",
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch activities: HTTP ${res.status}`);
    }
    const data = await res.json();
    if (Array.isArray(data) && data.length > 0) {
      return data;
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
  const res = await fetch(`${API_BASE_URL}/api/v1/clearances`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(
      `Evaluation failed (HTTP ${res.status}): ${errorText || res.statusText}`
    );
  }

  return await res.json();
}

export async function checkBackendHealth(): Promise<{
  status: string;
  cache_driver?: string;
  version?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`, {
      method: "GET",
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Backend offline or loading
  }
  return { status: "disconnected" };
}
