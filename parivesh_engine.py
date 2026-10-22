"""
parivesh_engine.py
------------------
Playwright browser automation, network request interception (Camunda DMN /evaluate),
Angular Material DOM manipulation, and clearance extraction engine for PARIVESH 2.0.
"""

import os
import re
import json
import base64
import tempfile
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

CAPTCHA_PNG = "current_captcha.png"


class DummyStatus:
    def info(self, msg): logger.info(msg)
    def warning(self, msg): logger.warning(msg)
    def error(self, msg): logger.error(msg)
    def success(self, msg): logger.info(msg)


# ── CAPTCHA Solver Helper ─────────────────────────────────────────────────────
def _try_onnx_solve(img_bytes):
    try:
        from captcha_solver import solve_captcha_from_bytes
        return solve_captcha_from_bytes(img_bytes)
    except Exception as e:
        logger.warning("CAPTCHA solve error: %s", e)
        return "", 0.0


# ── Angular Material Dropdown Selection ───────────────────────────────────────
def _select_mat_option(page, nth_select, option_text, timeout_ms=8000):
    """
    Selects an option from the nth mat-select on the page.
    Uses exact / distinctive prefix matching rather than a single ambiguous word.
    """
    clean_target = " ".join(option_text.strip().split())

    # Strategy 1: Standard Playwright click flow
    try:
        selects = page.locator("mat-select")
        selects.nth(nth_select).wait_for(state="visible", timeout=6000)
        trigger = selects.nth(nth_select)
        trigger.scroll_into_view_if_needed()
        trigger.click()
        page.wait_for_timeout(800)

        # Wait for overlay to open
        page.locator(".cdk-overlay-container").wait_for(state="visible", timeout=4000)
        page.wait_for_timeout(400)

        snippet = clean_target[:35] if len(clean_target) > 35 else clean_target
        opts = page.locator(".cdk-overlay-container mat-option")
        opt = opts.filter(has_text=snippet).first
        if not opt.is_visible():
            opt = opts.filter(has_text=clean_target).first
        if opt.is_visible():
            opt.click()
            page.wait_for_timeout(1000)
            logger.info("Strategy 1 OK: selected option matching '%s'", snippet)
            return True
    except Exception as e1:
        logger.warning("Strategy 1 failed for '%s': %s", clean_target[:20], e1)

    # Strategy 2: JS evaluate fallback with exact / highest-overlap matching
    try:
        clicked = page.evaluate(
            """(args) => {
                const [nth, targetStr] = args;
                const selects = document.querySelectorAll('mat-select');
                if (selects[nth]) selects[nth].click();
                const targetLower = targetStr.toLowerCase();
                const opts = Array.from(document.querySelectorAll('.cdk-overlay-container mat-option, mat-option'));

                // 1. Exact match
                let match = opts.find(o => o.textContent.trim().toLowerCase() === targetLower);
                // 2. StartsWith match
                if (!match) match = opts.find(o => o.textContent.trim().toLowerCase().startsWith(targetLower.slice(0, 30)));
                // 3. Includes match
                if (!match) match = opts.find(o => o.textContent.trim().toLowerCase().includes(targetLower.slice(0, 30)));
                if (match) {
                    match.click();
                    return true;
                }
                return false;
            }""",
            [nth_select, clean_target],
        )
        if clicked:
            page.wait_for_timeout(1000)
            logger.info("Strategy 2 OK: selected option matching '%s'", clean_target[:20])
            return True
    except Exception as e2:
        logger.warning("Strategy 2 failed: %s", e2)

    return False


# ── Canvas Extraction ─────────────────────────────────────────────────────────
def _capture_captcha_canvas(page):
    """Waits for the canvas to render, then extracts via toDataURL(). Returns PNG bytes or None."""
    try:
        page.locator("canvas").wait_for(state="visible", timeout=8000)
        page.wait_for_timeout(500)
    except Exception:
        pass

    try:
        b64 = page.evaluate("""() => {
            const canvas = document.querySelector('canvas');
            if (!canvas || canvas.width < 50) return null;
            const tmp = document.createElement('canvas');
            tmp.width  = canvas.width;
            tmp.height = canvas.height;
            const ctx = tmp.getContext('2d');
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, tmp.width, tmp.height);
            ctx.drawImage(canvas, 0, 0);
            return tmp.toDataURL('image/png').split(',')[1];
        }""")
        if b64:
            return base64.b64decode(b64)
    except Exception as e:
        logger.warning("canvas.toDataURL failed: %s", e)

    # Fallback: screenshot the captcha area
    try:
        elem = page.locator(".file-upload, div:has(> canvas)").first
        if elem.is_visible():
            return elem.screenshot()
    except Exception as e:
        logger.warning("Element screenshot fallback failed: %s", e)
    return None


# ── Result Extraction from DOM & Intercepted Payload ──────────────────────────
def _extract_results_from_page(page, intercepted_data=None):
    """
    Extracts clearance results from the PARIVESH results page.
    Supports:
      1. Intercepted Camunda DMN /evaluate API payload (100% full, un-truncated remarks)
      2. Live DOM parsing of the Tentative Clearances table
      3. Project summary, proximity layers, Toposheet No., and administrative boundary data
    """
    results = {"clearances": [], "administrative": [], "toposheet": "", "proximity": [], "project": {}}

    # 1. Primary: Intercepted Camunda DMN evaluate JSON response
    if intercepted_data and "dmn_result" in intercepted_data:
        res = intercepted_data["dmn_result"]
        req = intercepted_data.get("dmn_request", {})

        env_flag = req.get("envclear", {}).get("value", False)
        fc_flag = req.get("forclear", {}).get("value", False)
        wl_flag = req.get("wildlifeclear", {}).get("value", False)
        crz_flag = req.get("crz", {}).get("value", False)

        ec_rem = res.get("remark_ec", {}).get("value", "")
        fc_rem = res.get("remark_fc", {}).get("value", "")
        wl_rem = res.get("remark_wl", {}).get("value", "")
        crz_rem = res.get("remark_crz", {}).get("value", "")

        def determine_app(flag, remark):
            rem_lower = str(remark).lower()
            if flag:
                return "Yes"
            if "not falling" in rem_lower or "not covered" in rem_lower:
                return "No"
            if "falling in" in rem_lower or "covered under" in rem_lower:
                return "Yes"
            return "No"

        results["clearances"] = [
            {
                "S.No": "1",
                "Approval": "Environmental clearance",
                "Applicability": determine_app(env_flag, ec_rem),
                "Remarks": ec_rem
            },
            {
                "S.No": "2",
                "Approval": "Forest Clearance",
                "Applicability": determine_app(fc_flag, fc_rem),
                "Remarks": fc_rem
            },
            {
                "S.No": "3",
                "Approval": "Wildlife Clearance",
                "Applicability": determine_app(wl_flag, wl_rem),
                "Remarks": wl_rem
            },
            {
                "S.No": "4",
                "Approval": "Coastal Regulation Clearance",
                "Applicability": determine_app(crz_flag, crz_rem),
                "Remarks": crz_rem
            }
        ]

    # 2. Secondary / DOM Fallback: Parse Tentative Clearances table directly from DOM
    dom_rows = page.evaluate("""() => {
        const out = [];
        const tbls = Array.from(document.querySelectorAll('table'));
        const targetTable = tbls.find(t => {
            const text = (t.innerText || '').toLowerCase();
            return text.includes('approval') && text.includes('applicability');
        });

        if (!targetTable) return [];

        const rows = Array.from(targetTable.querySelectorAll('tr'));
        for (let i = 1; i < rows.length; i++) {
            const cells = Array.from(rows[i].querySelectorAll('th, td'));
            if (cells.length >= 3) {
                const sno = cells[0].innerText.trim();
                const approval = cells[1].innerText.trim();

                let app = "No";
                const cellText = cells[2].innerText.trim();
                if (/\\byes\\b/i.test(cellText)) {
                    app = "Yes";
                } else if (/\\bno\\b/i.test(cellText)) {
                    app = "No";
                }

                let remarks = "";
                if (cells.length >= 4) {
                    remarks = cells[3].innerText.replace(/\\bMore\\b/gi, '').trim();
                }

                if (approval && !/approval/i.test(approval)) {
                    out.push({
                        "S.No": sno || String(out.length + 1),
                        "Approval": approval,
                        "Applicability": app,
                        "Remarks": remarks
                    });
                }
            }
        }
        return out;
    }""")

    if not results["clearances"] and dom_rows:
        results["clearances"] = dom_rows
    elif results["clearances"] and dom_rows:
        # Merge DOM applicability with un-truncated DMN remarks
        for d_row in dom_rows:
            d_appr = d_row.get("Approval", "").lower()
            for r in results["clearances"]:
                if r.get("Approval", "").lower() in d_appr or d_appr in r.get("Approval", "").lower():
                    r["Applicability"] = d_row.get("Applicability", r["Applicability"])

    # 3. Project summary from report boxes or table
    proj_data = page.evaluate("""() => {
        const out = {};
        const boxes = document.querySelectorAll('div');
        for (const b of boxes) {
            if (b.children.length === 2) {
                const title = b.children[0].innerText.trim();
                const val = b.children[1].innerText.trim();
                if (['Project / Activity', 'Sub Activity', 'Project Capacity / Extent'].includes(title)) {
                    out[title] = val;
                }
            }
        }
        if (Object.keys(out).length > 0) return out;

        const tables = document.querySelectorAll('table');
        for (const tbl of tables) {
            const rows = tbl.querySelectorAll('tr');
            if (rows.length >= 2) {
                const hdrs = Array.from(rows[0].querySelectorAll('th, td')).map(c => c.innerText.trim());
                if (hdrs.includes('Project/Activity') || hdrs.includes('Sub Activity')) {
                    const vals = Array.from(rows[1].querySelectorAll('td')).map(c => c.innerText.trim());
                    hdrs.forEach((h, i) => { if (h) out[h] = vals[i] || ''; });
                    return out;
                }
            }
        }
        return {};
    }""")
    results["project"] = proj_data

    # 4. Proximity / spatial layers table
    prox_data = page.evaluate("""() => {
        const tables = document.querySelectorAll('table');
        for (const tbl of tables) {
            const rows = tbl.querySelectorAll('tr');
            const hdrs = rows.length > 0
                ? Array.from(rows[0].querySelectorAll('th,td')).map(c => c.innerText.trim())
                : [];
            if (hdrs.includes('Source') && hdrs.includes('Distance')) {
                const out = [];
                for (let i = 1; i < rows.length; i++) {
                    const cells = Array.from(rows[i].querySelectorAll('td')).map(c => c.innerText.trim());
                    if (cells.length >= 2 && cells[0]) out.push({Source: cells[0], Distance: cells[1]});
                }
                return out;
            }
        }
        return [];
    }""")
    results["proximity"] = prox_data

    # 5. Toposheet & Administrative Location
    loc_data = page.evaluate("""() => {
        const out = { toposheet: '', locations: [] };

        const tidEl = document.querySelector('#tid');
        if (tidEl) {
            out.toposheet = tidEl.innerText.replace(/\\s+/g, ' ').trim();
        }

        const geoTable = document.querySelector('#geoLocId');
        if (geoTable) {
            const stateRows = geoTable.querySelectorAll('tbody tr.state-row, tbody tr');
            stateRows.forEach(sr => {
                const stateEl = sr.querySelector('.state-cell strong, td.state-cell, td:first-child strong');
                const stateName = stateEl ? stateEl.innerText.trim() : '';

                const distRows = sr.querySelectorAll('.district-row');
                if (distRows.length > 0) {
                    distRows.forEach(dr => {
                        const distEl = dr.querySelector('.dist-value, .district-name');
                        const distName = distEl ? distEl.innerText.trim() : '';

                        const villages = Array.from(dr.querySelectorAll('.village-item'))
                            .map(v => v.innerText.replace(/,/g, '').trim())
                            .filter(Boolean);
                        const villageText = villages.length > 0 ? villages.join(', ') : (dr.querySelector('.village-list')?.innerText.trim() || '');

                        if (distName || villageText) {
                            out.locations.push({
                                State: stateName,
                                District: distName,
                                Village: villageText
                            });
                        }
                    });
                } else {
                    const cells = Array.from(sr.querySelectorAll('td'));
                    if (cells.length >= 3) {
                        out.locations.push({
                            State: cells[0].innerText.trim(),
                            District: cells[1].innerText.trim(),
                            Village: cells[2].innerText.trim()
                        });
                    }
                }
            });
        }
        return out;
    }""")
    if loc_data:
        results["toposheet"] = loc_data.get("toposheet", "")
        results["administrative"] = loc_data.get("locations", [])

    return results


# ── Full Automation Engine ────────────────────────────────────────────────────
def run_full_automated_lookup(
    activity_name, subactivity_name, capacity,
    location_mode, lat, lon, kml_bytes, kml_name,
    manual_captcha="", status_callback=None, session_state=None
):
    """
    Executes end-to-end evaluation:
    Launches Playwright headless Chromium, selects project parameters,
    uploads KML / coordinates, solves CAPTCHA, confirms GIS dialog, and extracts clearances.
    """
    status = status_callback if status_callback is not None else DummyStatus()
    status.info("Launching headless browser...")

    temp_kml_path = None
    if kml_bytes:
        temp_dir = tempfile.gettempdir()
        temp_kml_path = os.path.join(temp_dir, kml_name or "uploaded.kml")
        with open(temp_kml_path, "wb") as f:
            f.write(kml_bytes)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-web-security", "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page(viewport={"width": 1366, "height": 900})

        intercepted_data = {}

        def handle_response(response):
            try:
                if "evaluate" in response.url and response.status == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0 and ("remark_ec" in data[0] or "remark_fc" in data[0]):
                        intercepted_data["dmn_result"] = data[0]
                        logger.info("Captured DMN evaluate response: %s", data[0])
            except Exception:
                pass

        def handle_request(request):
            try:
                if "evaluate" in request.url and request.method == "POST":
                    post_data = request.post_data_json
                    if post_data and "variables" in post_data:
                        intercepted_data["dmn_request"] = post_data["variables"]
                        logger.info("Captured DMN evaluate request variables: %s", post_data["variables"])
            except Exception:
                pass

        page.on("response", handle_response)
        page.on("request", handle_request)

        # Intercept 100% accurate, case-sensitive CAPTCHA directly from canvas drawing
        page.add_init_script("""
            const orig = CanvasRenderingContext2D.prototype.fillText;
            CanvasRenderingContext2D.prototype.fillText = function(text) {
                if (text && text.length === 6) {
                    window.__PARIVESH_CAPTCHA__ = text;
                }
                return orig.apply(this, arguments);
            };
        """)

        try:
            status.info("Connecting to PARIVESH KYA Portal...")
            page.goto("https://parivesh.nic.in/kya/#/", timeout=45000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            # Remove blocking overlays (keep GIS dialog intact)
            page.evaluate("""() => {
                const mob = document.getElementById('mobiledev');
                if (mob) mob.remove();
                document.querySelectorAll('.modal-backdrop, #backdrop, [id*="backdrop"]').forEach(e => e.remove());
            }""")

            # ── 1. Activity Selection ─────────────────────────────────────────
            status.info(f"Selecting Activity: {activity_name}...")
            act_ok = _select_mat_option(page, 0, activity_name.strip())
            if not act_ok:
                status.warning("Activity selection all 3 strategies failed — form may use default.")
            page.wait_for_timeout(1500)

            # ── 2. Sub-Activity Selection ─────────────────────────────────────
            if subactivity_name and "No sub-activities" not in subactivity_name:
                status.info("Selecting Sub-Activity...")
                sub_ok = _select_mat_option(page, 1, subactivity_name.strip())
                if not sub_ok:
                    logger.warning("Sub-activity selection failed for '%s'", subactivity_name[:30])
                page.wait_for_timeout(800)

            # ── 3. Project Extent / Capacity ──────────────────────────────────
            if capacity:
                try:
                    status.info(f"Filling Project Capacity: {capacity}...")
                    cap_locator = page.locator("input[type='number'], input.mat-input-element, input[placeholder*='strip'], input[placeholder*='Capacity']").first
                    cap_locator.wait_for(state="visible", timeout=6000)
                    cap_locator.click()
                    cap_locator.fill(str(capacity))
                    page.wait_for_timeout(300)
                    page.evaluate(
                        """(val) => {
                            const inp = document.querySelector("input[type='number'], input.mat-input-element");
                            if (inp) {
                                inp.value = val;
                                inp.dispatchEvent(new Event('input', {bubbles: true}));
                                inp.dispatchEvent(new Event('change', {bubbles: true}));
                            }
                        }""",
                        str(capacity),
                    )
                    logger.info("Project Capacity filled: %s", capacity)
                except Exception as e:
                    logger.warning("Capacity fill failed: %s", e)

            # ── 4. Location Mode ──────────────────────────────────────────────
            if location_mode == "Upload KML" and temp_kml_path:
                status.info(f"Uploading KML: {os.path.basename(temp_kml_path)}...")
                try:
                    page.locator("mat-radio-button, [role='radio']").filter(has_text="Upload KML").first.click(force=True)
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                fi = page.locator("input[type='file']").first
                if fi.count() > 0:
                    fi.set_input_files(temp_kml_path)
                    page.wait_for_timeout(1500)
            else:
                status.info(f"Entering coordinates: ({lat}, {lon})...")
                try:
                    page.locator("mat-radio-button, [role='radio']").filter(has_text="Point Location").first.click(force=True)
                    page.wait_for_timeout(600)
                    # Dismiss disclaimer modal if shown
                    close_btn = page.locator("#staticBackdrop button:has-text('Close'), button[data-bs-dismiss='modal']").first
                    if close_btn.is_visible():
                        close_btn.click()
                        page.wait_for_timeout(400)
                except Exception:
                    pass

                # Convert decimal degrees to Degrees, Minutes, Seconds (DMS)
                try:
                    def _to_dms(deg_val):
                        d = int(deg_val)
                        rem = abs(deg_val - d) * 60
                        m = int(rem)
                        s = round((rem - m) * 60, 2)
                        return d, m, s

                    lat_d, lat_m, lat_s = _to_dms(lat)
                    lon_d, lon_m, lon_s = _to_dms(lon)

                    page.evaluate("""({lat_d, lat_m, lat_s, lon_d, lon_m, lon_s}) => {
                        function setVal(id, val) {
                            const el = document.getElementById(id);
                            if (el) {
                                el.value = val;
                                el.dispatchEvent(new Event('input', {bubbles: true}));
                                el.dispatchEvent(new Event('change', {bubbles: true}));
                            }
                        }
                        setVal('latDeg', lat_d);
                        setVal('latMin', lat_m);
                        setVal('latSec', lat_s);
                        setVal('lngDeg', lon_d);
                        setVal('lngMin', lon_m);
                        setVal('lngSec', lon_s);
                    }""", {"lat_d": lat_d, "lat_m": lat_m, "lat_s": lat_s, "lon_d": lon_d, "lon_m": lon_m, "lon_s": lon_s})
                    logger.info("DMS coordinates filled: Lat(%s° %s' %s\") Lon(%s° %s' %s\")", lat_d, lat_m, lat_s, lon_d, lon_m, lon_s)
                except Exception as e:
                    logger.warning("DMS input failed, trying direct inputs: %s", e)
                    lat_i = page.locator("input[placeholder*='Lat'], input[formcontrolname*='lat']").first
                    lon_i = page.locator("input[placeholder*='Lon'], input[formcontrolname*='lon'], input[placeholder*='Long']").first
                    if lat_i.is_visible() and lon_i.is_visible():
                        lat_i.fill(str(lat))
                        lon_i.fill(str(lon))

            # ── 5. CAPTCHA Solving ────────────────────────────────────────────
            status.info("Resolving CAPTCHA...")
            captcha_val = (manual_captcha or "").strip()

            if not captcha_val:
                page.wait_for_timeout(800)
                intercepted = page.evaluate("() => window.__PARIVESH_CAPTCHA__")
                if intercepted and len(intercepted) == 6:
                    captcha_val = intercepted
                    if session_state is not None:
                        session_state["last_captcha_text"] = captcha_val
                        session_state["last_captcha_conf"] = 1.0
                    logger.info("Captured CAPTCHA string via canvas hook: '%s'", captcha_val)

            if not captcha_val:
                captcha_bytes = _capture_captcha_canvas(page)
                if captcha_bytes:
                    with open(CAPTCHA_PNG, "wb") as f:
                        f.write(captcha_bytes)
                    captcha_auto_text, captcha_confidence = _try_onnx_solve(captcha_bytes)
                    captcha_val = captcha_auto_text
                    if session_state is not None:
                        session_state["last_captcha_text"] = captcha_auto_text
                        session_state["last_captcha_conf"] = captcha_confidence
                    logger.info("ddddocr fallback solved CAPTCHA: '%s'", captcha_val)

            if captcha_val:
                status.info(f"Entering CAPTCHA: {captcha_val}...")
                captcha_input = page.locator("input[placeholder='Enter Captcha'], input[placeholder*='Captcha'], input[placeholder*='captcha']").first
                if captcha_input.is_visible():
                    captcha_input.fill("")
                    captcha_input.fill(captcha_val)
                page.evaluate(
                    """(val) => {
                        const inp = document.querySelector('input[placeholder*="aptcha"], input[placeholder*="Enter"]');
                        if (inp) {
                            inp.value = val;
                            inp.dispatchEvent(new Event('input', {bubbles:true}));
                            inp.dispatchEvent(new Event('change', {bubbles:true}));
                        }
                    }""",
                    captcha_val,
                )
                page.wait_for_timeout(400)

            # ── 6. Form Submission ────────────────────────────────────────────
            status.info("Submitting form...")
            submit = page.locator("button:has-text('Upload & Submit'), button:has-text('Submit'), button:has-text('Proceed')").first
            submit.click(force=True)
            page.wait_for_timeout(2000)

            # ── 7. Handle GIS Confirmation Dialog ─────────────────────────────
            status.info("Waiting for GIS map confirmation...")
            try:
                proceed_btn = page.locator("#proceedId:not([disabled]), button:has-text('YES'):not([disabled])").first
                proceed_btn.wait_for(state="visible", timeout=35000)
                status.info("GIS Confirmation is ready! Clicking YES...")
                page.wait_for_timeout(500)
                proceed_btn.click(force=True)
                page.evaluate("() => document.getElementById('proceedId')?.click()")
                page.wait_for_timeout(1000)
            except Exception as e:
                logger.info("GIS YES button not found or already proceeded: %s", e)

            # ── 8. Wait for Bharatmaps GIS & Tentative Clearances Table ────────
            status.info("Waiting for Bharatmaps spatial analysis & clearance evaluation...")
            for i in range(25):
                if intercepted_data.get("dmn_result"):
                    logger.info("DMN evaluate result intercepted on attempt %d!", i)
                    break
                has_clearance_rows = page.evaluate("""() => {
                    const tbls = Array.from(document.querySelectorAll('table'));
                    const target = tbls.find(t => {
                        const txt = (t.innerText || '').toLowerCase();
                        return txt.includes('approval') && txt.includes('applicability');
                    });
                    if (target && target.querySelectorAll('tr').length >= 4) {
                        return true;
                    }
                    return false;
                }""")
                if has_clearance_rows:
                    logger.info("Tentative Clearances table with 4+ rows detected in DOM!")
                    break
                page.wait_for_timeout(1000)

            page.wait_for_timeout(1500)

            # ── 9. Capture GIS Map Screenshot ─────────────────────────────────
            os.makedirs("debug", exist_ok=True)
            map_path = os.path.join("debug", "parivesh_map_view.png")
            try:
                map_el = page.locator(".esri-view, #map, div.col-sm-7:has(canvas), div:has(> canvas.esri-display-object)").first
                if map_el.is_visible():
                    map_el.screenshot(path=map_path)
            except Exception as me:
                logger.warning("Map screenshot error: %s", me)

            # Save debug artifacts
            page.screenshot(path=os.path.join("debug", "debug_parivesh_page.png"))
            with open(os.path.join("debug", "debug_parivesh_dom.html"), "w", encoding="utf-8") as f:
                f.write(page.content())

            # ── 10. Extract Results ───────────────────────────────────────────
            status.info("Extracting clearances...")
            results = _extract_results_from_page(page, intercepted_data)
            if os.path.exists(map_path):
                results["map_png"] = map_path

            if results["clearances"]:
                status.success(f"Retrieved {len(results['clearances'])} clearance entries!")
            else:
                status.warning("No clearances found — debug artifacts saved to debug/")

            browser.close()
            return results

        except Exception as exc:
            status.error(f"Execution halted: {exc}")
            try:
                os.makedirs("debug", exist_ok=True)
                page.screenshot(path=os.path.join("debug", "debug_parivesh_error.png"))
                browser.close()
            except Exception:
                pass
            return None
