"use client";

import React, { useState, useEffect } from "react";
import {
  Compass,
  FileCheck2,
  Download,
  Copy,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  MapPin,
  Upload,
  ArrowRight,
  Database,
  ExternalLink,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import {
  MasterActivity,
  MasterSubActivity,
  ClearanceResponse,
  ClearanceItem,
} from "../types/clearance";
import {
  fetchMasterActivities,
  fetchSubActivities,
  evaluateClearances,
  checkBackendHealth,
} from "../services/api";

import defaultActivities from "../data/activities.json";
import defaultSubactivities from "../data/subactivities.json";
import thresholdUnitsData from "../data/threshold_units.json";

export default function Home() {
  // Master data: pre-populate all 56 official sectors immediately
  const [activities, setActivities] = useState<MasterActivity[]>(defaultActivities);
  
  // Pre-populate initial sub-activities for Airports (ID 29)
  const initialSubs = (defaultSubactivities as Record<string, MasterSubActivity[]>)["29"] || [];
  const [subActivities, setSubActivities] = useState<MasterSubActivity[]>(initialSubs);

  // Form State
  const [selectedActivityName, setSelectedActivityName] = useState<string>("Airports");
  const [selectedActivityId, setSelectedActivityId] = useState<number | undefined>(29);
  const [selectedSubActivityName, setSelectedSubActivityName] = useState<string>(
    initialSubs[0]?.name || "All New projects including Airstrips for commercial use"
  );
  const [capacity, setCapacity] = useState<string>("250");
  const [capacityUnit, setCapacityUnit] = useState<string>("sqmtr");
  const [capacityParamLabel, setCapacityParamLabel] = useState<string>("Project Extent / Capacity");
  const [availableUnits, setAvailableUnits] = useState<{ unit: string; param?: string }[]>([
    { unit: "sqmtr", param: "Built up Area" },
    { unit: "Km", param: "Length" },
    { unit: "Ha", param: "Area" },
    { unit: "MW", param: "Capacity" },
    { unit: "TPA", param: "Production Capacity" },
    { unit: "KLPD", param: "Capacity" },
  ]);

  // Location State
  const [locationMode, setLocationMode] = useState<"Point Location" | "Upload KML">("Point Location");
  const [latitude, setLatitude] = useState<number>(21.1976);
  const [longitude, setLongitude] = useState<number>(72.8356);
  const [kmlContent, setKmlContent] = useState<string>("");
  const [kmlFilename, setKmlFilename] = useState<string>("");

  // System & Evaluation State
  const [backendStatus, setBackendStatus] = useState<string>("checking");
  const [cacheDriver, setCacheDriver] = useState<string>("memory");
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingStep, setLoadingStep] = useState<string>("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [report, setReport] = useState<ClearanceResponse | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Initial Load: Check Backend and Load Activities
  useEffect(() => {
    async function init() {
      const health = await checkBackendHealth();
      setBackendStatus(health.status);
      if (health.cache_driver) setCacheDriver(health.cache_driver);

      const acts = await fetchMasterActivities();
      if (acts && acts.length > 0) {
        setActivities(acts);
      }
    }
    init();
  }, []);

  // When selected activity changes, confirm with backend/cache
  useEffect(() => {
    async function loadSubs() {
      if (selectedActivityId) {
        const subs = await fetchSubActivities(selectedActivityId);
        if (subs && subs.length > 0) {
          setSubActivities(subs);
        }
      }
    }
    loadSubs();
  }, [selectedActivityId]);

  // Dynamically update Unit and Parameter label based on selected Subactivity / Activity
  useEffect(() => {
    const subObj = subActivities.find(
      (s) => (s.name || s.sub_activity_name)?.trim().toLowerCase() === selectedSubActivityName?.trim().toLowerCase()
    );
    const subId = subObj?.id ? String(subObj.id) : null;
    const actId = selectedActivityId ? String(selectedActivityId) : null;

    let matched: { unit: string; param?: string }[] = [];
    if (subId && (thresholdUnitsData.by_subactivity as Record<string, { unit: string; param?: string }[]>)[subId]) {
      matched = (thresholdUnitsData.by_subactivity as Record<string, { unit: string; param?: string }[]>)[subId];
    } else if (actId && (thresholdUnitsData.by_activity as Record<string, { unit: string; param?: string }[]>)[actId]) {
      matched = (thresholdUnitsData.by_activity as Record<string, { unit: string; param?: string }[]>)[actId];
    }

    if (matched && matched.length > 0) {
      setAvailableUnits(matched);
      // Auto-select official unit
      setCapacityUnit(matched[0].unit);
      if (matched[0].param) {
        setCapacityParamLabel(matched[0].param);
      } else {
        setCapacityParamLabel("Project Extent / Capacity");
      }
    } else {
      setAvailableUnits([
        { unit: "sqmtr", param: "Built up Area" },
        { unit: "Km", param: "Length" },
        { unit: "Ha", param: "Area" },
        { unit: "MW", param: "Capacity" },
        { unit: "TPA", param: "Production Capacity" },
        { unit: "KLPD", param: "Capacity" },
      ]);
      setCapacityParamLabel("Project Extent / Capacity");
    }
  }, [selectedSubActivityName, selectedActivityId, subActivities]);

  // Handle Activity Select Change (Instant swap from subactivities catalog)
  const handleActivityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const actName = e.target.value;
    setSelectedActivityName(actName);
    const found = activities.find(
      (a) => (a.name || a.activity_name)?.trim().toLowerCase() === actName.trim().toLowerCase()
    );
    const newId = found?.id || found?.activity_id;
    setSelectedActivityId(newId);

    if (newId) {
      const preloaded = (defaultSubactivities as Record<string, MasterSubActivity[]>)[String(newId)];
      if (preloaded && preloaded.length > 0) {
        setSubActivities(preloaded);
        setSelectedSubActivityName(preloaded[0].name || "General");
      } else {
        setSubActivities([{ id: 0, name: "General (All categories)" }]);
        setSelectedSubActivityName("General (All categories)");
      }
    }
  };

  // Handle KML File Upload
  const handleKmlUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setKmlFilename(file.name);
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        setKmlContent(text);
      };
      reader.readAsText(file);
    }
  };

  // Presets
  const applyPreset = (name: string, lat: number, lon: number, cap: string, act: string) => {
    setLatitude(lat);
    setLongitude(lon);
    setCapacity(cap);
    setSelectedActivityName(act);
    const found = activities.find((a) => (a.name || a.activity_name)?.trim().toLowerCase() === act.trim().toLowerCase());
    const newId = found?.id || found?.activity_id;
    setSelectedActivityId(newId);
    if (newId) {
      const preloaded = (defaultSubactivities as Record<string, MasterSubActivity[]>)[String(newId)];
      if (preloaded && preloaded.length > 0) {
        setSubActivities(preloaded);
        setSelectedSubActivityName(preloaded[0].name || "General");
      }
    }
  };

  // Trigger Clearance Evaluation
  const handleEvaluate = async () => {
    setLoading(true);
    setErrorMsg(null);
    setLoadingStep("Connecting to PARIVESH 2.0 KYA Service...");

    const steps = [
      "Connecting to PARIVESH 2.0 KYA Service...",
      "Resolving CAPTCHA & Angular form states...",
      "Executing Camunda DMN decision evaluation...",
      "Intersecting Bharatmaps spatial boundary layers...",
      "Synthesizing statutory remarks & compliance matrix...",
    ];

    let stepIdx = 0;
    const interval = setInterval(() => {
      stepIdx = (stepIdx + 1) % steps.length;
      setLoadingStep(steps[stepIdx]);
    }, 4500);

    try {
      const res = await evaluateClearances({
        activity_name: selectedActivityName,
        activity_id: selectedActivityId,
        subactivity_name: selectedSubActivityName,
        capacity,
        capacity_unit: capacityUnit,
        location_mode: locationMode,
        latitude,
        longitude,
        kml_content: kmlContent,
        kml_filename: kmlFilename,
      });

      clearInterval(interval);
      setReport(res);
      setLoading(false);
    } catch (err: any) {
      clearInterval(interval);
      setLoading(false);
      setErrorMsg(err.message || "Failed to complete clearance evaluation");
    }
  };

  // Export CSV
  const downloadCSV = () => {
    if (!report?.clearances) return;
    const headers = "S.No,Approval,Applicability,Remarks\n";
    const rows = report.clearances
      .map(
        (c) =>
          `"${c["S.No"]}","${c.Approval}","${c.Applicability}","${c.Remarks.replace(/"/g, '""')}"`
      )
      .join("\n");
    const blob = new Blob([headers + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `parivesh_clearances_${Date.now()}.csv`;
    link.click();
  };

  // Export JSON
  const downloadJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `parivesh_kya_report_${Date.now()}.json`;
    link.click();
  };

  // Copy Summary
  const copySummary = () => {
    if (!report) return;
    const summary = `PARIVESH 2.0 KYA Evaluation Summary:
Project: ${selectedActivityName} - ${selectedSubActivityName} (Capacity: ${capacity} ${capacityUnit})
Coordinates: Lat ${latitude}, Lon ${longitude} | Toposheet: ${report.toposheet || "N/A"}
Clearances:
${report.clearances.map((c) => `- ${c.Approval}: ${c.Applicability}`).join("\n")}`;

    navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  // KPI Calculations
  const totalCount = report?.clearances.length || 0;
  const applicableCount =
    report?.clearances.filter(
      (c) => c.Applicability?.trim().toLowerCase() === "yes"
    ).length || 0;
  const notRequiredCount =
    report?.clearances.filter(
      (c) => c.Applicability?.trim().toLowerCase() === "no"
    ).length || 0;

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* ── Top Header / Navigation ────────────────────────────────────── */}
      <header
        style={{
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          background: "rgba(7, 11, 20, 0.8)",
          backdropFilter: "blur(16px)",
          position: "sticky",
          top: 0,
          zIndex: 50,
          padding: "14px 28px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #0284c7 0%, #10b981 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 16px rgba(56, 189, 248, 0.4)",
            }}
          >
            <Compass size={22} color="#ffffff" />
          </div>
          <div>
            <h1
              style={{
                fontSize: "1.05rem",
                fontWeight: 800,
                letterSpacing: "-0.01em",
                color: "#ffffff",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              PARIVESH 2.0 KYA
              <span
                style={{
                  fontSize: "0.7rem",
                  background: "rgba(56, 189, 248, 0.15)",
                  color: "#38bdf8",
                  padding: "2px 8px",
                  borderRadius: "6px",
                  border: "1px solid rgba(56, 189, 248, 0.3)",
                }}
              >
                PRO STACK
              </span>
            </h1>
            <p style={{ fontSize: "0.76rem", color: "#94a3b8" }}>
              Environmental & Spatial Clearance Intelligence Suite (FastAPI + Vercel)
            </p>
          </div>
        </div>

        {/* Status Indicators */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              background: "rgba(15, 23, 42, 0.6)",
              padding: "6px 12px",
              borderRadius: "20px",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              fontSize: "0.76rem",
              color: "#cbd5e1",
            }}
          >
            <span
              className={backendStatus === "healthy" ? "pulse-dot" : ""}
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: backendStatus === "healthy" ? "#10b981" : "#f59e0b",
                display: "inline-block",
              }}
            />
            <span>
              Backend:{" "}
              <strong style={{ color: backendStatus === "healthy" ? "#34d399" : "#fbbf24" }}>
                {backendStatus === "healthy" ? "FastAPI Online" : "Ready / Standby"}
              </strong>
            </span>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>|</span>
            <Database size={13} color="#38bdf8" />
            <span>Cache: <strong style={{ color: "#38bdf8" }}>{cacheDriver}</strong></span>
          </div>
        </div>
      </header>

      {/* ── Main Body Container ────────────────────────────────────────── */}
      <main style={{ maxWidth: "1560px", margin: "0 auto", padding: "28px", width: "100%", flex: 1 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "24px", alignItems: "start" }}>
          
          {/* ── Left Column: Configuration Console ──────────────────────── */}
          <div className="glass-panel" style={{ padding: "24px" }}>
            <div className="section-tag">
              <span className="section-tag-num">01</span>
              <span>Project Classification</span>
            </div>

            {/* Activity Dropdown */}
            <div style={{ marginBottom: "18px" }}>
              <label className="input-label" htmlFor="activity-select">
                Project Sector / Activity *
              </label>
              <select
                id="activity-select"
                className="input-field"
                value={selectedActivityName}
                onChange={handleActivityChange}
              >
                {activities.map((a, idx) => {
                  const name = a.name || a.activity_name || `Activity ${idx}`;
                  return (
                    <option key={idx} value={name} style={{ background: "#0f172a", color: "#ffffff" }}>
                      {name}
                    </option>
                  );
                })}
              </select>
            </div>

            {/* Sub-Activity Dropdown */}
            <div style={{ marginBottom: "18px" }}>
              <label className="input-label" htmlFor="subactivity-select">
                Sub Activity Category *
              </label>
              <select
                id="subactivity-select"
                className="input-field"
                value={selectedSubActivityName}
                onChange={(e) => setSelectedSubActivityName(e.target.value)}
              >
                {subActivities.length > 0 ? (
                  subActivities.map((s, idx) => {
                    const name =
                      s.name || s.sub_activity_name || s.subActivityName || `Category ${idx}`;
                    return (
                      <option key={idx} value={name} style={{ background: "#0f172a", color: "#ffffff" }}>
                        {name}
                      </option>
                    );
                  })
                ) : (
                  <option value="General" style={{ background: "#0f172a", color: "#ffffff" }}>
                    General (No sub-activities specified)
                  </option>
                )}
              </select>
            </div>

            {/* Project Capacity / Extent Input with Direct Unit Addon */}
            <div style={{ marginBottom: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <label className="input-label" htmlFor="capacity-input" style={{ marginBottom: 0 }}>
                  Project Capacity/Extent *
                </label>
                {capacityParamLabel && capacityParamLabel !== "Project Extent / Capacity" && (
                  <span style={{ fontSize: "11px", color: "rgba(56, 189, 248, 0.9)", fontWeight: 500 }}>
                    Parameter: {capacityParamLabel}
                  </span>
                )}
              </div>

              <div style={{ position: "relative", display: "flex", alignItems: "stretch" }}>
                <input
                  id="capacity-input"
                  type="text"
                  className="input-field"
                  value={capacity}
                  onChange={(e) => setCapacity(e.target.value)}
                  placeholder={`Enter ${capacityParamLabel || "capacity"}`}
                  style={{
                    borderTopRightRadius: 0,
                    borderBottomRightRadius: 0,
                    borderRight: "none",
                    flex: 1,
                  }}
                />
                
                {availableUnits.length > 1 ? (
                  <select
                    id="unit-input"
                    value={capacityUnit}
                    onChange={(e) => setCapacityUnit(e.target.value)}
                    title="Select measurement unit"
                    style={{
                      background: "rgba(15, 23, 42, 0.9)",
                      border: "1px solid rgba(56, 189, 248, 0.3)",
                      borderLeft: "none",
                      borderTopRightRadius: "8px",
                      borderBottomRightRadius: "8px",
                      color: "#38bdf8",
                      padding: "0 14px",
                      fontSize: "13px",
                      fontWeight: 600,
                      cursor: "pointer",
                      outline: "none",
                    }}
                  >
                    {availableUnits.map((u, i) => (
                      <option key={i} value={u.unit} style={{ background: "#0f172a", color: "#f8fafc" }}>
                        ({u.unit})
                      </option>
                    ))}
                  </select>
                ) : (
                  <span
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: "rgba(15, 23, 42, 0.9)",
                      border: "1px solid rgba(56, 189, 248, 0.3)",
                      borderLeft: "none",
                      borderTopRightRadius: "8px",
                      borderBottomRightRadius: "8px",
                      color: "#38bdf8",
                      padding: "0 16px",
                      fontSize: "13px",
                      fontWeight: 600,
                      userSelect: "none",
                    }}
                  >
                    ({capacityUnit})
                  </span>
                )}
              </div>
            </div>

            {/* Section 02: Geospatial Coordinates */}
            <div className="section-tag" style={{ marginTop: "10px" }}>
              <span className="section-tag-num">02</span>
              <span>Geospatial Coordinates & Bounds</span>
            </div>

            {/* Location Mode Tabs */}
            <div
              style={{
                display: "flex",
                background: "rgba(10, 16, 31, 0.6)",
                padding: "4px",
                borderRadius: "8px",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                marginBottom: "16px",
              }}
            >
              <button
                type="button"
                onClick={() => setLocationMode("Point Location")}
                style={{
                  flex: 1,
                  padding: "8px 12px",
                  borderRadius: "6px",
                  background: locationMode === "Point Location" ? "#0284c7" : "transparent",
                  color: locationMode === "Point Location" ? "#ffffff" : "#94a3b8",
                  border: "none",
                  fontWeight: 600,
                  fontSize: "0.82rem",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "6px",
                  transition: "all 0.2s ease",
                }}
              >
                <MapPin size={14} />
                Point Location
              </button>
              <button
                type="button"
                onClick={() => setLocationMode("Upload KML")}
                style={{
                  flex: 1,
                  padding: "8px 12px",
                  borderRadius: "6px",
                  background: locationMode === "Upload KML" ? "#0284c7" : "transparent",
                  color: locationMode === "Upload KML" ? "#ffffff" : "#94a3b8",
                  border: "none",
                  fontWeight: 600,
                  fontSize: "0.82rem",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "6px",
                  transition: "all 0.2s ease",
                }}
              >
                <Upload size={14} />
                Upload KML Polygon
              </button>
            </div>

            {/* Point Location Inputs */}
            {locationMode === "Point Location" ? (
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "14px" }}>
                  <div>
                    <label className="input-label" htmlFor="lat-input">
                      Latitude (°N)
                    </label>
                    <input
                      id="lat-input"
                      type="number"
                      step="0.0001"
                      className="input-field"
                      value={latitude}
                      onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
                    />
                  </div>
                  <div>
                    <label className="input-label" htmlFor="lon-input">
                      Longitude (°E)
                    </label>
                    <input
                      id="lon-input"
                      type="number"
                      step="0.0001"
                      className="input-field"
                      value={longitude}
                      onChange={(e) => setLongitude(parseFloat(e.target.value) || 0)}
                    />
                  </div>
                </div>

                {/* Quick Presets */}
                <div style={{ marginBottom: "22px" }}>
                  <span style={{ fontSize: "0.72rem", color: "#64748b", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                    QUICK SAMPLE PRESETS:
                  </span>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    <button
                      type="button"
                      onClick={() => applyPreset("Hazira Port", 21.1114, 72.6342, "1000", "Ports, Harbours, Break waters, Dredging")}
                      className="btn-secondary"
                      style={{ fontSize: "0.74rem", padding: "4px 8px" }}
                    >
                      ⚓ Gujarat Hazira Port
                    </button>
                    <button
                      type="button"
                      onClick={() => applyPreset("Navi Mumbai Airport", 18.9902, 73.0691, "500", "Airports")}
                      className="btn-secondary"
                      style={{ fontSize: "0.74rem", padding: "4px 8px" }}
                    >
                      ✈️ Navi Mumbai Airport
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              /* KML Upload Zone */
              <div
                style={{
                  border: "2px dashed rgba(56, 189, 248, 0.3)",
                  borderRadius: "10px",
                  padding: "24px 16px",
                  textAlign: "center",
                  background: "rgba(2, 6, 23, 0.4)",
                  marginBottom: "20px",
                }}
              >
                <Upload size={32} color="#38bdf8" style={{ margin: "0 auto 8px" }} />
                <p style={{ fontSize: "0.86rem", color: "#e2e8f0", fontWeight: 600 }}>
                  Upload Project Boundary (.kml)
                </p>
                <p style={{ fontSize: "0.74rem", color: "#94a3b8", marginTop: "4px" }}>
                  Polygon or boundary shape exported from Google Earth or GIS
                </p>
                <input
                  type="file"
                  accept=".kml"
                  id="kml-upload"
                  onChange={handleKmlUpload}
                  style={{ display: "none" }}
                />
                <label
                  htmlFor="kml-upload"
                  className="btn-secondary"
                  style={{ marginTop: "12px", cursor: "pointer" }}
                >
                  Choose .kml file
                </label>
                {kmlFilename && (
                  <p style={{ marginTop: "10px", fontSize: "0.78rem", color: "#34d399" }}>
                    ✓ Loaded: <strong>{kmlFilename}</strong> ({kmlContent.length} bytes)
                  </p>
                )}
              </div>
            )}

            {/* Error Message */}
            {errorMsg && (
              <div
                style={{
                  background: "rgba(244, 63, 94, 0.12)",
                  border: "1px solid rgba(244, 63, 94, 0.35)",
                  borderRadius: "8px",
                  padding: "12px",
                  marginBottom: "16px",
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  fontSize: "0.82rem",
                  color: "#fda4af",
                }}
              >
                <AlertCircle size={18} color="#f43f5e" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Submit Action Button */}
            <button
              id="evaluate-btn"
              type="button"
              className="btn-primary"
              disabled={loading || (locationMode === "Upload KML" && !kmlContent)}
              onClick={handleEvaluate}
            >
              {loading ? (
                <>
                  <div
                    style={{
                      width: "18px",
                      height: "18px",
                      border: "2px solid rgba(255,255,255,0.3)",
                      borderTopColor: "#ffffff",
                      borderRadius: "50%",
                      animation: "spin 1s linear infinite",
                    }}
                  />
                  <span>Evaluating Clearances...</span>
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  <span>EVALUATE TENTATIVE CLEARANCES</span>
                </>
              )}
            </button>
          </div>

          {/* ── Right Column: Clearance Intelligence & Compliance Report ── */}
          <div className="glass-panel" style={{ padding: "24px" }}>
            <div className="section-tag">
              <span className="section-tag-num">03</span>
              <span>Clearance Intelligence & Statutory Report</span>
            </div>

            {/* Loading Indicator with Stage Progression */}
            {loading && (
              <div
                style={{
                  padding: "48px 24px",
                  textAlign: "center",
                  background: "rgba(2, 6, 23, 0.4)",
                  borderRadius: "12px",
                  border: "1px solid rgba(56, 189, 248, 0.2)",
                }}
              >
                <div
                  style={{
                    width: "48px",
                    height: "48px",
                    margin: "0 auto 16px",
                    border: "3px solid rgba(56, 189, 248, 0.2)",
                    borderTopColor: "#38bdf8",
                    borderRadius: "50%",
                    animation: "spin 1s linear infinite",
                  }}
                />
                <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", marginBottom: "8px" }}>
                  Automating PARIVESH 2.0 Evaluation
                </h3>
                <p style={{ fontSize: "0.86rem", color: "#38bdf8", fontWeight: 600 }}>
                  {loadingStep}
                </p>
                <p style={{ fontSize: "0.76rem", color: "#64748b", marginTop: "12px" }}>
                  Executing Camunda DMN decision table & zero-click CAPTCHA resolution...
                </p>
              </div>
            )}

            {/* Empty State when no report yet */}
            {!loading && !report && (
              <div
                style={{
                  padding: "54px 28px",
                  textAlign: "center",
                  background: "rgba(10, 16, 31, 0.3)",
                  borderRadius: "12px",
                  border: "1px dashed rgba(255, 255, 255, 0.1)",
                }}
              >
                <div
                  style={{
                    width: "60px",
                    height: "60px",
                    borderRadius: "16px",
                    background: "rgba(56, 189, 248, 0.1)",
                    border: "1px solid rgba(56, 189, 248, 0.25)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 auto 16px",
                  }}
                >
                  <Layers size={28} color="#38bdf8" />
                </div>
                <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#f8fafc", marginBottom: "6px" }}>
                  Awaiting Project Specifications
                </h3>
                <p style={{ fontSize: "0.82rem", color: "#94a3b8", maxWidth: "440px", margin: "0 auto 24px" }}>
                  Select your industrial activity, configure capacity metrics, and provide geospatial coordinates to trigger tentative clearance evaluation across all 4 statutory pillars.
                </p>

                {/* 4 Pillars Preview */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(2, 1fr)",
                    gap: "10px",
                    textAlign: "left",
                    maxWidth: "460px",
                    margin: "0 auto",
                  }}
                >
                  <div style={{ background: "rgba(15, 23, 42, 0.6)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontSize: "0.76rem", fontWeight: 700, color: "#38bdf8" }}>🌿 Environment (EC)</div>
                    <div style={{ fontSize: "0.7rem", color: "#64748b" }}>EIA Notification 2006 Schedule</div>
                  </div>
                  <div style={{ background: "rgba(15, 23, 42, 0.6)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontSize: "0.76rem", fontWeight: 700, color: "#10b981" }}>🌲 Forest Land (FC)</div>
                    <div style={{ fontSize: "0.7rem", color: "#64748b" }}>Van Sanrakshan Adhiniyam 1980</div>
                  </div>
                  <div style={{ background: "rgba(15, 23, 42, 0.6)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontSize: "0.76rem", fontWeight: 700, color: "#f59e0b" }}>🐾 Wildlife (NBWL)</div>
                    <div style={{ fontSize: "0.7rem", color: "#64748b" }}>ESZ & Protected Area 10km Buffer</div>
                  </div>
                  <div style={{ background: "rgba(15, 23, 42, 0.6)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontSize: "0.76rem", fontWeight: 700, color: "#818cf8" }}>🌊 Coastal Zone (CRZ)</div>
                    <div style={{ fontSize: "0.7rem", color: "#64748b" }}>CRZ Notification 2019 Buffer</div>
                  </div>
                </div>
              </div>
            )}

            {/* Results View */}
            {!loading && report && (
              <div>
                {/* Cache & Execution Banner */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    background: "rgba(15, 23, 42, 0.5)",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                    borderRadius: "8px",
                    padding: "8px 14px",
                    marginBottom: "16px",
                    fontSize: "0.78rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <Clock size={14} color="#94a3b8" />
                    <span>
                      Execution time: <strong>{report.execution_time_seconds}s</strong>
                    </span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <Database size={14} color={report.cached ? "#34d399" : "#38bdf8"} />
                    <span>
                      Cache:{" "}
                      <strong style={{ color: report.cached ? "#34d399" : "#38bdf8" }}>
                        {report.cached ? "HIT (Instant Upstash/Redis)" : "MISS (Live Evaluated)"}
                      </strong>
                    </span>
                  </div>
                </div>

                {/* ── 4-Metric KPI Stat Strip ───────────────────────────── */}
                <div className="kpi-grid">
                  <div className="kpi-card">
                    <div className="kpi-label">Total Pillars</div>
                    <div className="kpi-value">{totalCount}</div>
                  </div>
                  <div className="kpi-card kpi-applicable">
                    <div className="kpi-label">Applicable</div>
                    <div className="kpi-value green">{applicableCount}</div>
                  </div>
                  <div className="kpi-card kpi-exempt">
                    <div className="kpi-label">Not Required</div>
                    <div className="kpi-value" style={{ color: "#94a3b8" }}>
                      {notRequiredCount}
                    </div>
                  </div>
                  <div className="kpi-card kpi-toposheet">
                    <div className="kpi-label">Toposheet No.</div>
                    <div className="kpi-value cyan">{report.toposheet || "N/A"}</div>
                  </div>
                </div>

                {/* ── Tentative Clearances Table ────────────────────────── */}
                <div style={{ marginBottom: "20px" }}>
                  <h4 style={{ fontSize: "0.92rem", fontWeight: 700, color: "#ffffff", marginBottom: "8px" }}>
                    📋 Tentative Clearances Summary
                  </h4>
                  <div
                    style={{
                      borderRadius: "10px",
                      overflow: "hidden",
                      border: "1px solid rgba(255, 255, 255, 0.08)",
                      background: "rgba(10, 16, 31, 0.6)",
                    }}
                  >
                    <table className="clearance-table">
                      <thead>
                        <tr>
                          <th style={{ width: "50px" }}>S.No</th>
                          <th style={{ width: "220px" }}>Approval Category</th>
                          <th style={{ width: "130px" }}>Applicability</th>
                          <th>Legal Remarks & Mandate</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.clearances.map((c, idx) => {
                          const isYes =
                            c.Applicability?.trim().toLowerCase() === "yes";
                          return (
                            <tr key={idx}>
                              <td style={{ color: "#64748b", fontWeight: 600 }}>{c["S.No"]}</td>
                              <td style={{ fontWeight: 600, color: "#f8fafc" }}>{c.Approval}</td>
                              <td>
                                <span className={isYes ? "badge-yes" : "badge-no"}>
                                  {isYes ? "APPLICABLE" : "NOT REQUIRED"}
                                </span>
                              </td>
                              <td style={{ color: "#cbd5e1", fontSize: "0.84rem", lineHeight: "1.4" }}>
                                {c.Remarks || "No statutory remarks recorded."}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* ── Administrative Bounds Card ────────────────────────── */}
                {report.administrative && report.administrative.length > 0 && (
                  <div style={{ marginBottom: "20px" }}>
                    <h4 style={{ fontSize: "0.92rem", fontWeight: 700, color: "#ffffff", marginBottom: "8px" }}>
                      📍 Administrative Location & Survey Bounds
                    </h4>
                    <div
                      style={{
                        borderRadius: "10px",
                        overflow: "hidden",
                        border: "1px solid rgba(255, 255, 255, 0.08)",
                        background: "rgba(10, 16, 31, 0.6)",
                      }}
                    >
                      <table className="clearance-table">
                        <thead>
                          <tr>
                            <th>State</th>
                            <th>District</th>
                            <th>Village / Survey Bounds</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report.administrative.map((a, idx) => (
                            <tr key={idx}>
                              <td style={{ fontWeight: 600, color: "#f8fafc" }}>{a.State}</td>
                              <td style={{ color: "#cbd5e1" }}>{a.District}</td>
                              <td style={{ color: "#94a3b8" }}>{a.Village}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* ── Proximity Spatial Layers ───────────────────────────── */}
                {report.proximity && report.proximity.length > 0 && (
                  <div style={{ marginBottom: "20px" }}>
                    <h4 style={{ fontSize: "0.92rem", fontWeight: 700, color: "#ffffff", marginBottom: "8px" }}>
                      🌐 Proximity Spatial Layers (Bharatmaps)
                    </h4>
                    <div
                      style={{
                        borderRadius: "10px",
                        overflow: "hidden",
                        border: "1px solid rgba(255, 255, 255, 0.08)",
                        background: "rgba(10, 16, 31, 0.6)",
                      }}
                    >
                      <table className="clearance-table">
                        <thead>
                          <tr>
                            <th>Spatial Feature / Sensitive Zone</th>
                            <th>Calculated Proximity Buffer</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report.proximity.map((p, idx) => (
                            <tr key={idx}>
                              <td style={{ fontWeight: 600, color: "#f8fafc" }}>{p.Source}</td>
                              <td style={{ color: "#38bdf8" }}>{p.Distance}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* ── Action & Export Toolbar ────────────────────────────── */}
                <div
                  style={{
                    display: "flex",
                    gap: "10px",
                    flexWrap: "wrap",
                    borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                    paddingTop: "16px",
                  }}
                >
                  <button type="button" onClick={downloadCSV} className="btn-secondary">
                    <Download size={14} />
                    Download CSV
                  </button>
                  <button type="button" onClick={downloadJSON} className="btn-secondary">
                    <Download size={14} />
                    Download JSON Report
                  </button>
                  <button type="button" onClick={copySummary} className="btn-secondary">
                    {copied ? <CheckCircle2 size={14} color="#34d399" /> : <Copy size={14} />}
                    {copied ? "Copied!" : "Copy Summary"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* CSS Animation Keyframes */}
      <style jsx global>{`
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
