/**
 * TypeScript types for PARIVESH 2.0 KYA Evaluation API.
 */

export interface MasterActivity {
  id?: number;
  activity_id?: number;
  name?: string;
  activity_name?: string;
  description?: string;
  sectorEntity?: {
    sectorName?: string;
    sectorCode?: string;
  };
}

export interface MasterSubActivity {
  id?: number;
  sub_activity_id?: number;
  name?: string;
  sub_activity_name?: string;
  subActivityName?: string;
  description?: string;
}

export interface ClearanceItem {
  "S.No": string;
  Approval: string;
  Applicability: string;
  Remarks: string;
}

export interface AdministrativeLocation {
  State: string;
  District: string;
  Village: string;
}

export interface ProximityLayer {
  Source: string;
  Distance: string;
}

export interface ClearanceResponse {
  success: boolean;
  message: string;
  cached: boolean;
  execution_time_seconds: number;
  clearances: ClearanceItem[];
  toposheet: string;
  administrative: AdministrativeLocation[];
  proximity: ProximityLayer[];
  project: Record<string, string>;
  map_png_url?: string;
}

export interface ClearanceRequestPayload {
  activity_name: string;
  activity_id?: number;
  subactivity_name: string;
  subactivity_id?: number;
  capacity: string;
  capacity_unit?: string;
  location_mode: "Point Location" | "Upload KML";
  latitude?: number;
  longitude?: number;
  kml_content?: string;
  kml_filename?: string;
}
