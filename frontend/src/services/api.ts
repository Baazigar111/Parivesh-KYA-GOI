/**
 * api.ts
 * ------
 * Client service to interface with FastAPI backend (Cloud Run, ECS, or local dev).
 */

import {
  MasterActivity,
  MasterSubActivity,
  ClearanceRequestPayload,
  ClearanceResponse,
} from "../types/clearance";

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
    return await res.json();
  } catch (err) {
    console.warn("FastAPI activities request failed:", err);
    // Fallback to essential sectors if backend is not yet started
    return [
      { id: 4, name: "Airports" },
      { id: 52, name: "Aerial Ropeways" },
      { id: 18, name: "Building and Construction projects" },
      { id: 25, name: "Coal Washeries" },
      { id: 31, name: "Distilleries" },
      { id: 45, name: "Highways" },
      { id: 58, name: "Mining of Minerals" },
      { id: 62, name: "Oil and Gas Transportation Pipeline" },
      { id: 74, name: "Ports, Harbours, Break waters, Dredging" },
      { id: 89, name: "Thermal Power Plants" },
    ];
  }
}

export async function fetchSubActivities(
  activityId: number
): Promise<MasterSubActivity[]> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/subactivities?activity_id=${activityId}`,
      {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }
    );
    if (!res.ok) {
      throw new Error(`Failed to fetch sub-activities: HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.warn(`Sub-activities request failed for activity ${activityId}:`, err);
    return [];
  }
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
