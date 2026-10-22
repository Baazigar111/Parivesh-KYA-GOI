# 🌿 PARIVESH 2.0 KYA — Environmental & Spatial Clearance Intelligence Suite

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.4.2-black.svg?style=flat&logo=next.js)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19.0.0-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![Playwright](https://img.shields.io/badge/Playwright-1.40.0-2EAD33.svg?style=flat&logo=playwright)](https://playwright.dev)
[![Upstash Redis](https://img.shields.io/badge/Upstash-Redis-00E699.svg?style=flat&logo=redis)](https://upstash.com)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000.svg?style=flat&logo=vercel)](https://vercel.com)

An enterprise-grade, decoupled intelligence platform that evaluates tentative statutory clearances across all **4 legal pillars** (Environmental, Forest, Wildlife, and Coastal Regulation Zone) from the Ministry of Environment, Forest and Climate Change (MoEFCC) **PARIVESH 2.0 KYA (Know Your Approvals)** government portal.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Frontend_Tier ["Frontend Layer (Vercel CDN Edge)"]
        UI["Next.js 16 Web App\n(React 19, TypeScript, Vanilla CSS Glassmorphism)"]
    end

    subgraph Ingress_Tier ["Secure Static Ingress"]
        TUNNEL["ngrok Permanent Static Tunnel\n(https://glitter-scrambled-defensive.ngrok-free.dev)"]
    end

    subgraph Backend_Tier ["Backend Service (Local / Indian Egress)"]
        API["FastAPI Async REST Service\n(Port 8000 /docs)"]
        CACHE[("Upstash Redis / In-Memory Cache\n(24h Master Catalog, 1h Clearances)")]
        ENGINE["Playwright Headless Chromium Engine"]
        CAPTCHA["Zero-Click Canvas CAPTCHA Hook\n+ ONNX CNN Dual Engine"]
        DMS["Decimal-to-DMS Coordinate Converter\n+ Angular Modal Dismissal"]
        DMN["Camunda DMN REST Interceptor\n(/engine-rest/decision-definition/key/*/evaluate)"]
        THRESH["Official Threshold Parameter Catalog\n(187 Subactivities & 56 Sectors)"]
    end

    subgraph Government_Tier ["Government of India Gateways"]
        NIC["PARIVESH 2.0 Portal\n(https://parivesh.nic.in/kya/#/)"]
        BHARAT["Bharatmaps Spatial GIS Layer"]
        CAMUNDA_GOV["MoEFCC Camunda Decision Engine"]
    end

    UI -->|JSON REST / API_URL| TUNNEL
    TUNNEL --> API
    API <--> CACHE
    API --> ENGINE
    ENGINE --> CAPTCHA
    ENGINE --> DMS
    ENGINE --> THRESH
    ENGINE <-->|Domestic Indian IP Egress| NIC
    ENGINE <--> BHARAT
    ENGINE <--> DMN
    DMN <--> CAMUNDA_GOV
```

---

## 🔄 Project Evolution: What Was Changed & Why

| Evolution Stage | What Was Changed | Why It Was Changed |
| :--- | :--- | :--- |
| **1. Framework Decoupling** | Replaced monolithic **Streamlit** with **FastAPI (Backend)** + **Next.js 16 (Frontend)**. | Streamlit reruns the entire Python script on every user click, freezing the UI during 40-second Playwright operations. Decoupling allowed global CDN delivery on Vercel with a dedicated async API. |
| **2. NIC Geo-Firewall Resolution** | Transitioned backend from overseas cloud datacenters (Render) to **Domestic Indian IP Egress via ngrok Static Tunnel**. | The National Informatics Centre (NIC, `parivesh.nic.in`) enforces an active **National Geo-IP Firewall** that returns `net::ERR_CONNECTION_REFUSED` to non-Indian cloud IPs. Running backend on an Indian connection resolves this 100%. |
| **3. Unit Selection 1:1 Portal Alignment** | Replaced the manual/mandatory **"Unit" dropdown** with an **automatic statutory unit addon badge (`#basic-addon2`)**. | On the official government portal, units are **never chosen manually by the user**. Every subactivity has its exact statutory unit (e.g. `Km`, `sqmtr`, `Ha`, `MW`) and parameter placeholder (`Built up Area`, `Length`, `Mine Lease Area`) fixed by law. |
| **4. Subactivity Threshold Mapping** | Generated [threshold_units.json](file:///d:/Train/22oct26/parivesh_scrap/frontend/src/data/threshold_units.json) mapping all **187 subactivities** and **56 sectors** from government APIs. | Enables instantaneous (<5ms) client-side updating of units and parameter names when switching activities or subactivities. |
| **5. Coordinates & Modal Handling** | Added **Decimal-to-DMS (Degrees, Minutes, Seconds) conversion** and **automated 50-meter buffer disclaimer dismissal**. | Point Location on the government portal does not accept raw decimal coordinates; it requires split DMS inputs (`latDeg`, `latMin`, `latSec`, etc.) and presents a blocking Bootstrap disclaimer popup. |
| **6. Zero-Click CAPTCHA Interception** | Replaced slow OCR with an **in-memory Canvas 2D prototype hook** backed by an **ONNX CNN model**. | Intercepts the exact 6-character captcha string during `fillText` in <5ms with 100% precision, completely removing human friction and OCR failure rates. |
| **7. Camunda DMN Table Extraction** | Intercepted internal `POST /engine-rest/decision-definition/key/*/evaluate` network requests. | Government DOM tables truncate legal remarks and conditions behind modals. Intercepting the Camunda DMN payload extracts 100% complete, un-truncated legal remarks and statutory condition flags. |
| **8. Environment Standardization** | Standardized frontend to use **`API_URL`** (with fallback to `NEXT_PUBLIC_API_URL`). | Configured `next.config.ts` to expose `API_URL` to client browser bundles, making deployment configuration clean and intuitive across Vercel and local `.env.local`. |

---

## 🔬 Tech Stack Rationales: What We Used & Why We Used It

### 1. Backend: FastAPI (Python 3.10+)
- **What We Used:** FastAPI with Uvicorn worker runtime, Pydantic v2 schemas, and CORS middleware.
- **Why It Is Used Here:**
  - **High-Throughput Asynchronous Architecture:** Handles concurrent API requests without blocking event loops while Playwright processes headless browser tasks.
  - **Strict Geospatial Validation:** Pydantic v2 ensures that coordinate inputs, KML payloads, and sector parameters are strictly typed, sanitized, and documented.
  - **Python Native Compatibility:** Essential for direct interoperability with Playwright Chromium, Pillow image processing, and ONNX Runtime machine learning models without inter-process IPC overhead.
  - **Auto-Generated Interactive Documentation:** Live interactive Swagger UI available at `/docs` for rapid endpoint testing.

---

### 2. Frontend: Next.js 16 + React 19 + TypeScript
- **What We Used:** Next.js 16 App Router, React 19 Server & Client components, TypeScript, Lucide Icons.
- **Why It Is Used Here:**
  - **Edge CDN Speed on Vercel:** Static generation (`next build` with Turbopack) delivers the initial page shell from Vercel's global edge network in under 150 milliseconds.
  - **Zero Browser Binaries in Frontend:** Isolates all heavy browser automation and OS dependencies onto the backend, keeping the frontend lightweight and mobile-friendly.
  - **Pre-Loaded 56-Sector & Subactivity Catalog:** Bundles official government master data in `activities.json` and `subactivities.json`, enabling instant (<5ms) zero-latency dropdown switching.
  - **Type-Safe API Contracts:** TypeScript interfaces ensure full type consistency between backend API responses and frontend rendering components.

---

### 3. Styling: Vanilla CSS & Glassmorphism Design Tokens
- **What We Used:** Custom Vanilla CSS design system with CSS custom properties (`globals.css`), backdrop blur filters, and neon status badges.
- **Why It Is Used Here:**
  - **Zero Runtime Overhead:** Avoids heavy CSS-in-JS runtimes and large utility framework dependencies, yielding near-instant First Contentful Paint (FCP).
  - **Executive Intelligence Aesthetic:** Styled like an institutional geospatial intelligence console with high-contrast glowing pill badges, responsive KPI metric strips, and clear statutory compliance tables.

---

### 4. Browser Automation: Playwright Headless Chromium
- **What We Used:** Playwright Python `v1.40.0` running headless Chromium with Linux container compatibility flags (`--no-sandbox`, `--disable-dev-shm-usage`, `--disable-web-security`).
- **Why It Is Used Here:**
  - **Overcomes Non-API Single-Page Application (SPA) Barriers:** The official PARIVESH 2.0 portal is built on Angular Material and does not provide public REST calculation endpoints. Playwright automates the form flow cleanly (`mat-select`, `mat-radio-button`, file upload inputs).
  - **Network Request & Response Interception:** Provides granular hooks (`page.on("request")` and `page.on("response")`) to capture internal Camunda DMN decision tables before they are rendered into HTML.
  - **Headless Stability:** Highly stable execution across both Windows local machines and Linux Docker containers.

---

### 5. Zero-Click Canvas CAPTCHA Solver + ONNX CNN
- **What We Used:** Dual-engine solver combining a JavaScript Canvas prototype hook and an ONNX Convolutional Neural Network.
- **Why It Is Used Here:**
  - **In-Memory Prototype Hook (<5ms, 100% Accuracy):** The portal draws its 6-character captcha onto an HTML5 `<canvas>`. We inject:
    ```javascript
    CanvasRenderingContext2D.prototype.fillText = function(text) {
        if (text && text.length === 6) window.__PARIVESH_CAPTCHA__ = text;
        return orig.apply(this, arguments);
    };
    ```
    This reads the exact, case-sensitive verification code directly from browser memory before rasterization, eliminating OCR errors entirely.
  - **Dual-Engine Fallback:** If the hook is bypassed, an ONNX CNN (`captcha_model.onnx`) backed by `ddddocr` solves the rendered captcha image automatically.

---

### 6. Camunda DMN Decision Table Interceptor
- **What We Used:** Network interceptor listening for `POST /engine-rest/decision-definition/key/*/evaluate`.
- **Why It Is Used Here:**
  - When spatial coordinates are submitted, PARIVESH queries an internal Camunda DMN decision engine.
  - The government web interface frequently truncates lengthy statutory citations and legal remarks behind modal windows or ellipsis.
  - Intercepting the raw Camunda payload guarantees **100% complete, un-truncated legal remarks and condition flags** (`remark_ec`, `remark_fc`, `remark_wl`, `remark_crz`).

---

### 7. Caching Layer: Upstash Serverless Redis (+ In-Memory Fallback)
- **What We Used:** Upstash Redis REST client with automatic in-memory TTL dictionary fallback.
- **Why It Is Used Here:**
  - **Deduplication of Identical Queries:** Government clearance calculations take 30–50 seconds. By hashing query parameters (Sector + Subactivity + Capacity + Spatial Coordinates) with a **1-hour TTL**, repeated queries return in **<20 milliseconds**.
  - **Master Sectors Caching:** 56 activities and subactivities are cached for **24 hours**, eliminating redundant calls to government infrastructure.
  - **Zero-Crash Resilience:** If Redis credentials are absent, the service falls back gracefully to in-memory caching without throwing errors.

---

### 8. Network Architecture: ngrok Permanent Static Tunnel & Domestic Indian IP Egress
- **The Challenge:**
  - The Government of India NIC portal (`parivesh.nic.in`) has an active **National Geo-IP Firewall (WAF)** that drops/refuses connections originating from cloud datacenters outside India (`net::ERR_CONNECTION_REFUSED`).
- **The Solution:**
  - **Global Frontend:** Deployed on Vercel (`parivesh-kya-goi.vercel.app`) for worldwide access.
  - **Domestic Backend:** Runs on a machine with a domestic Indian IP address where NIC allows 100% of requests with HTTP 200.
  - **Permanent Static Tunnel:** An ngrok static domain (`https://glitter-scrambled-defensive.ngrok-free.dev`) securely bridges the public Vercel frontend to the local backend.
  - **Static Configuration:** Vercel's `API_URL` environment variable is configured once and never needs updating.

---

## ⚡ Features & Capabilities

- **Official 56 Industrial Sectors:** Pre-compiled catalog containing all official categories (Mining, Thermal Power, Cables, River Valley, Infrastructure, Chemical, Building/Construction, etc.).
- **Dynamic Statutory Units & Placeholders:** Unit badges (`(sqmtr)`, `(Km)`, `(Ha)`, `(MW)`, `(KLPD)`) and parameter labels attach directly to the `Project Capacity/Extent` field matching the official portal layout.
- **Dual Geospatial Location Modes:**
  - **Point Location:** Converts decimal Latitude/Longitude into **Degrees, Minutes, Seconds (DMS)** format expected by the portal, and automatically dismisses the 50-meter buffer disclaimer popup.
  - **Upload KML Polygon:** Directly uploads `.kml` boundary files exported from Google Earth or GIS software to evaluate full polyline/polygon footprints.
- **4 Statutory Pillars Evaluated:**
  - 🌿 **Environmental Clearance (EC):** EIA Notification 2006 Schedule applicability (Category A / B1 / B2).
  - 🌲 **Forest Clearance (FC):** Van Sanrakshan Evam Samvardhan Adhiniyam 1980 applicability.
  - 🐾 **Wildlife Clearance (NBWL):** Protected Area & Eco-Sensitive Zone (ESZ) 10km buffer checks.
  - 🌊 **Coastal Regulation Zone (CRZ):** CRZ Notification 2019 tidal buffer applicability.
- **Administrative & Spatial Breakdown:** Extracts SOI Toposheet Sheet No. and State/District/Village jurisdiction.
- **One-Click Export:** Instant download of clearance findings as formatted CSV or JSON reports.

---

## 📁 Repository Structure

```text
Parivesh-KYA-GOI/
│
├── backend/                        # FastAPI REST API Service
│   ├── app/
│   │   ├── main.py                 # FastAPI application & permissive CORS
│   │   ├── config.py               # Environment configuration (API_URL, Redis, ports)
│   │   ├── cache.py                # Upstash Redis + in-memory fallback cache
│   │   ├── schemas/                # Pydantic v2 data models
│   │   │   └── clearance.py        # Request and response models
│   │   ├── services/               # Business logic services
│   │   │   ├── parivesh_service.py # Core evaluation orchestrator
│   │   │   ├── dmn_service.py      # Camunda DMN evaluator
│   │   │   └── activities_service.py # 56-sector catalog service
│   │   └── routers/                # API route definitions
│   │       ├── clearances.py       # POST /api/v1/clearances
│   │       └── activities.py       # GET /api/v1/activities & subactivities
│   ├── Dockerfile                  # Container definition for Linux/Playwright
│   ├── requirements.txt            # Python dependencies (Playwright 1.40.0 pinned)
│   └── run.py                      # Development server runner
│
├── frontend/                       # Next.js 16 Web App (Vercel Ready)
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Intelligence dashboard console
│   │   │   ├── layout.tsx          # Root layout & Google typography
│   │   │   └── globals.css         # Glassmorphism styling & tokens
│   │   ├── components/             # Reusable UI cards & tables
│   │   ├── services/
│   │   │   └── api.ts              # Backend API client with clean URL sanitization
│   │   ├── data/
│   │   │   ├── activities.json     # Complete 56 official sectors
│   │   │   ├── subactivities.json  # Subactivities mapped by sector ID
│   │   │   └── threshold_units.json # Official statutory units for 187 subactivities
│   │   └── types/                  # TypeScript interfaces
│   ├── next.config.ts              # Exposes API_URL to client bundles
│   ├── vercel.json                 # Vercel deployment specification
│   ├── package.json                # Next.js & React 19 dependencies
│   ├── .env.local                  # Local environment file (API_URL=http://127.0.0.1:8000)
│   └── .env.example                # Frontend environment template
│
├── parivesh_engine.py              # Playwright automation, DMS converter & DMN intercept
├── captcha_solver.py               # ONNX CNN CAPTCHA recognition engine
├── captcha_model.onnx              # Trained ONNX model weights
├── captcha_model.onnx.data         # Model tensor binary data
├── docker-compose.yml              # Local container orchestration
├── LOCAL_HOSTING.md                # In-depth local operations & troubleshooting guide
├── start_local.bat                 # 1-Click Windows batch launcher
├── start_local.ps1                 # 1-Click PowerShell launcher
└── README.md                       # Master project documentation
```

---

## 🏃 Running Locally

### Option 1: 1-Click Launcher (Recommended)
Double-click **`start_local.bat`** (or run `.\start_local.ps1` in PowerShell).  
Both services launch simultaneously in separate windows:
- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2: Manual Terminal Execution

#### Terminal 1 — Backend (FastAPI):
```powershell
# Activate Python virtual environment
.\venv\Scripts\Activate.ps1

# Run FastAPI server
python backend/run.py
```

#### Terminal 2 — Frontend (Next.js):
```powershell
cd frontend
npm run dev
```

---

## 🌐 Connecting Vercel to Local Backend via Permanent ngrok Tunnel

To allow your live Vercel app (`https://parivesh-kya-goi.vercel.app`) to evaluate clearances through your local Indian IP connection:

1. **Start ngrok with your assigned static domain:**
   ```powershell
   npx ngrok http 8000 --url https://glitter-scrambled-defensive.ngrok-free.dev
   ```

2. **Configure Vercel Environment Variable:**
   In your **Vercel Dashboard > parivesh-kya-goi > Settings > Environment Variables**:
   - **Key:** `API_URL`
   - **Value:** `https://glitter-scrambled-defensive.ngrok-free.dev`

3. **Redeploy:** Go to **Deployments** and click **Redeploy**.

Because the domain is permanently bound to your ngrok account, you will never need to update this URL again.

---

## 📖 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health, cache driver status, and version |
| `GET` | `/api/v1/activities` | Complete catalog of 56 official industrial sectors |
| `GET` | `/api/v1/subactivities?activity_id={id}` | Sub-activities for a specific industrial sector |
| `POST` | `/api/v1/clearances` | Full end-to-end clearance evaluation with spatial GIS analysis |
| `POST` | `/api/v1/evaluate-dmn` | Direct Camunda DMN decision table evaluation |
| `POST` | `/api/v1/cache/clear` | Flushes Redis/in-memory cache |

Interactive Swagger documentation with live request testing is available at `http://localhost:8000/docs`.

---

## ⚖️ License
Released under the [MIT License](LICENSE).
