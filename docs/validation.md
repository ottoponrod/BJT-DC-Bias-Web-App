# Validation — BJT DC Bias Web App (Lab 03)

เว็บแอปรองรับ 3 โหมดไบอัส: **Voltage Divider**, **Fixed Bias** และ
**Emitter Bias** โดยทุกโหมดใช้แบบจำลอง Forward-Active (β และ VBE คงที่)
และแปลงหน่วยตัวต้านทานที่จุดรับข้อมูลครั้งเดียว (kΩ × 1000 = Ω)

## 1. ค่าอ้างอิงที่คำนวณด้วยมือ

ค่ากลางที่ทุกโหมดใช้ร่วมกัน: VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V

### 1.1 Voltage Divider Bias (A1)

R1 = 100 kΩ, R2 = 22 kΩ, RE = 1 kΩ

| ปริมาณ | สมการ | ค่า |
|---|---|---|
| VTH | VCC·R2/(R1+R2) | 2.1639 V |
| RTH | R1·R2/(R1+R2) | 18.033 kΩ |
| IB | (VTH−VBE)/(RTH+(β+1)RE) | 12.2986 µA |
| IC | β·IB | 1.2299 mA |
| IE | (β+1)·IB | 1.2422 mA |
| VE | IE·RE | 1.2422 V |
| VB | VE+VBE | 1.9422 V |
| VC | VCC−IC·RC | 9.2943 V |
| VCE | VC−VE | 8.0522 V |

Region: **Active** (VCE = 8.05 V > 1.0 V)

### 1.2 Fixed Bias (A2) — ค่าอ้างอิงอิสระของโหมดใหม่

RB = 1 MΩ = 1,000 kΩ = 1,000,000 Ω, ไม่มี RE (VE = 0 V)

| ปริมาณ | สมการ | ค่า |
|---|---|---|
| IB | (VCC−VBE)/RB = (12−0.70)/1,000,000 | 11.3000 µA |
| IC | β·IB = 100 × 11.3000 µA | 1.1300 mA |
| IE | (β+1)·IB = 101 × 11.3000 µA | 1.1413 mA |
| VE | 0 (อิมิตเตอร์ต่อลงกราวด์) | 0.000 V |
| VB | VE+VBE | 0.700 V |
| VC | VCC−IC·RC = 12 − 1.1300 mA × 2.2 kΩ | 9.5140 V |
| VCE | VC−VE | 9.5140 V |

### 1.3 Emitter Bias (A3, A4)

RB = 1 MΩ, RC = 2.2 kΩ

| ปริมาณ | A3: RE = 1 kΩ | A4: RE = 2 kΩ |
|---|---|---|
| IB | (12−0.70)/(1,000,000 + 101×1,000) = 10.2634 µA | (12−0.70)/(1,000,000 + 101×2,000) = 9.4010 µA |
| IC | 1.02634 mA | 0.94010 mA |
| IE | 1.03660 mA | 0.94950 mA |
| VE | 1.03660 V | 1.89900 V |
| VC | 9.74205 V | 9.93178 V |
| VCE | 8.70545 V | 8.03278 V |

**คำทำนาย A4:** เมื่อ RE เพิ่มจาก 1 kΩ เป็น 2 kΩ ตัวหาร
`RB + (β+1)RE` โตขึ้น ทำให้ IB และ IC **ลดลง** (ไม่ใช่เพิ่มขึ้น)
ผลจริงบนเว็บลดจาก 1.026 mA เป็น 0.940 mA ตรงกับคำทำนาย

## 2. ผลตรวจ A1–A5 ด้วยเบราว์เซอร์จริง

เครื่องมือ: OpenCode Browser (Chromium) เปิด <http://127.0.0.1:5000/>
กรอกค่าผ่านฟอร์มจริง กดปุ่ม Calculate DC Bias และอ่านค่าจากตารางผลลัพธ์
ทุกกรณีเป็น HTTP 200 และหน้าเว็บไม่ล้ม

| # | โหมด / อินพุต | IC ที่คาดหวัง | IC จริง | VCE ที่คาดหวัง | VCE จริง | ผล | หลักฐาน |
|---|---|---|---|---|---|---|---|
| A1 | Divider: R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | 1.230 mA | **1.230 mA** | 8.052 V | **8.052 V** | ผ่าน | `docs/evidence/lab03/A1-divider.jpg` |
| A2 | Fixed: RB=1000 kΩ (1 MΩ), ไม่กรอก RE | 1.130 mA | **1.130 mA** | 9.514 V | **9.514 V** | ผ่าน | `docs/evidence/lab03/A2-fixed.jpg` |
| A3 | Emitter: RB=1000 kΩ, RE=1 kΩ | 1.026 mA | **1.026 mA** | 8.705 V | **8.705 V** | ผ่าน | `docs/evidence/lab03/A3-emitter-re1k.jpg` |
| A4 | Emitter: เหมือน A3 แต่ RE=2 kΩ | 0.940 mA | **0.940 mA** | 8.033 V | **8.033 V** | ผ่าน (IC ลดลงตามคำทำนาย) | `docs/evidence/lab03/A4-emitter-re2k.jpg` |
| A5 | Fixed: RB=0 | error `RB ต้องมากกว่า 0 Ω` | **`RB ต้องมากกว่า 0 Ω`** | ไม่แสดงผล | ไม่มีตารางผล/แบนเนอร์ | ผ่าน | `docs/evidence/lab03/A5-fixed-rb0-error.jpg` |

ค่าความคลาดเคลื่อนสูงสุดที่ยอมรับ: |ΔIC| ≤ 0.01 mA และ |ΔVCE| ≤ 0.02 V
ผลจริงตรงกับค่าอ้างอิงที่ตำแหน่งทศนิยม 3 ตำแหน่งทุกกรณี (Δ = 0.000)

**ตรวจซ้ำรอบสุดท้าย (17 พ.ย. 2026, 18:42–18:43):** รัน A1–A5 ใหม่ทั้งหมดบน
Flask ที่รันโค้ดชุดปัจจุบัน (commit `50e94c4`) ผลตรงกับตารางเดิมทุกช่อง
และรัน A3 ซ้ำอีกครั้งได้ `IC 1.026 mA / VCE 8.705 V` เท่าเดิม (ยืนยันว่าทำซ้ำได้)
ภาพหลักฐานใน `docs/evidence/lab03/` ถูกแทนที่ด้วยภาพจากรอบนี้
เซิร์ฟเวอร์บันทึก `POST /calculate HTTP/1.1 200` ทุกครั้ง รวมถึงกรณี A5 (RB=0)
จึงยืนยันได้ว่าข้อความ error มาจาก Flask ไม่ใช่การบล็อกที่ฟอร์มในเบราว์เซอร์

### 2.1 สิ่งที่ตรวจเพิ่มในเบราว์เซอร์

- ฟอร์มเปลี่ยนช่องตามโหมด: Fixed แสดงเฉพาะ `rb` (ไม่มี `r1`, `r2`, `re`)
  และ Emitter แสดง `rb` + `re` (ไม่มี `r1`, `r2`)
- ปุ่ม **เปลี่ยนโหมด** มี `formnovalidate` ทำให้สลับโหมดได้แม้ช่องอื่นว่าง
  (แก้ regression ที่ปุ่มถูก HTML required บล็อก)
- A5: หลังส่ง RB=0 หน้าเว็บแสดงเฉพาะข้อความ error ไม่มีตารางหรือแบนเนอร์
  ของผลรอบก่อนค้างอยู่
- หน่วย Ω ใช้ได้กับทุกโหมด: กรอก RB=1000000, RC=2200, unit=Ω ให้ผลเท่ากับ
  การกรอกหน่วย kΩ

## 3. ผลการทดสอบอัตโนมัติ

คำสั่ง: `python -m unittest discover -s tests -v`

```
Ran 50 tests in 0.121s

OK
```

- `tests/test_dc_bias.py` — 22 tests: ค่าอ้างอิง Divider เดิม, validation,
  cutoff/saturation/near-saturation, NaN/∞, โหมด Fixed/Emitter (ค่าอ้างอิง,
  RE มากขึ้นทำให้ IC ลดลง, RB/RE ≤ 0, cutoff)
- `tests/test_web.py` — 28 tests: GET/POST เดิมทั้งหมด, mode selector,
  การสลับโหมด, `formnovalidate`, ผล Fixed/Emitter จาก Flask, หน่วย Ω,
  โหมดที่ไม่รู้จัก, error RB=0 โดยไม่มีผลค้าง, และแผนภาพ SVG ของแต่ละโหมด

## 4. ข้อจำกัดของแบบจำลอง

- ใช้ Forward-Active Approximation: β คงที่, VBE คงที่, ไม่คิด Early effect
- ไม่ใช่ ngspice/SPICE — ค่าที่ได้เป็นผลของสมการมือ ไม่ใช่ผลจำลองวงจรจริง
- Fixed bias ไม่มี RE จึงไวต่อ β มาก (IC = β·IB) และอาจอิ่มตัวง่ายกว่าโหมดอื่น
- เมื่อ VTH ≤ VBE (Divider) หรือ VCC ≤ VBE (Fixed/Emitter) ระบบรายงาน
  cutoff; เมื่อ VCE ≤ 0.3 V รายงาน saturation พร้อม warning ว่าแบบจำลอง
  Forward-Active ใช้ไม่ได้

---

## Lab 04 — SPICE simulator validation

### Environment

- Flask app served from the repository root with `.venv\Scripts\python.exe app.py`.
- Browser: in-app Chromium at `http://127.0.0.1:5000/`.
- Simulator: ngspice 47, verified by running a real batch netlist. Windows
  `--version` switches produce no output, so version confirmation is by the
  installed 47.x executable and successful `.op` / `.ac` / `.tran` runs.
- Transistor model: `QNPN NPN(BF=100 IS=1e-14 VAF=100)`. This is a
  self-defined reference model documented in the app; it is **not** an
  instructor-supplied or instructor-verified model.
- Reference circuit: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ,
  RL 10 kΩ, CIN = COUT = 10 µF, source 10 mV peak at 1 kHz.

### Task 4 — Impeccable critique and polish

#### Method

The Impeccable critique was run as a dual-agent assessment:

- **Assessment A (design review):** isolated subagent, rubric-based review of
  `templates/index.html`, `static/style.css`, and `static/app.js` plus live
  browser inspection.
- **Assessment B (detector/browser evidence):** isolated subagent running the
  Impeccable CLI source scan and URL scans at 1280×900 and 390×844, plus a
  browser-overlay attempt.

Assessment B could not attach the Impeccable overlay from its isolated session:
the browser returned
`[browser.disconnected] No desktop browser is connected to this session...`.
No overlay result is claimed. The evidence used instead is the CLI detector
output plus browser inspection from the parent session and Assessment A.

A stale-template issue was found during the critique: the Flask process had
cached the pre-Task-3 template, so the served HTML lacked Lab 04 while the CSS
was fresh. The server was restarted before any screenshots or browser evidence
were recorded.

#### Detector findings

| Scan | Before polish | After polish |
| --- | --- | --- |
| Source `templates/index.html` | exit 2; 1 finding: `flat-type-hierarchy` (warning); CLI advisory that the Jinja `url_for` CSS path cannot be resolved | exit 2; same 1 finding and same unresolved-path advisory |
| Rendered page 1280×900 | exit 2; 2 findings: `unbalanced-heading` (advisory), `side-tab` (warning) | exit 0; `[]` |
| Rendered page 390×844 | exit 2; 6 findings: `unbalanced-heading`, `straggler`, `side-tab`, `straggler`, `nested-cards`, `flat-type-hierarchy` | exit 0; `[]` |

The remaining source finding is a scanner artifact: the source scanner cannot
resolve `{{ url_for('static', filename='style.css') }}`, so it reports flat
heading sizes from default styles. The rendered page has a clear type scale and
zero findings at both requested viewports.

#### UI-only changes

- Grouped SPICE inputs into labelled fieldsets: Analysis, Bias network,
  Coupling capacitors, Source &amp; sweep, Units.
- Added numeric constraints and units to the SPICE inputs.
- Replaced the long status strip with a compact `role="status"` /
  `aria-live="polite"` region; engine and model details moved into a
  disclosure.
- Added a pending state that disables Run Simulation and announces
  “Running ngspice…” without inventing results.
- Added horizontal scroll wrappers and hints for Bode/transient SVG plots.
- Fixed the intermediate-width layout and removed the side-tab status border.
- Shortened the empty-state copy that produced a mobile straggler.
- Updated the footer to state both Lab 03 and Lab 04 scope while retaining the
  assignment context in a disclosure.

#### Before/after captures

| Viewport | Before | After |
| --- | --- | --- |
| Desktop 1280×900 full page | `docs/captures/before/1280x900-full.png` | `docs/captures/after/1280x900-full.png` |
| Mobile 390×844 full page | `docs/captures/before/390x844-full.png` | `docs/captures/after/390x844-full.png` |
| Canonical desktop pair | `docs/captures/ui-before.png` | `docs/captures/ui-after.png` |

#### Task 4 browser regression (B1-style)

| Check | Input | Expected | Observed | Status |
| --- | --- | --- | --- | --- |
| Divider bias | defaults: VCC 12, R1 100, R2 22, RC 2.2, RE 1, β 100, VBE 0.7 | `1.230` mA IC, `8.052` V VCE, Active | `IC 1.230 mA`, `VCE 8.052 V`, `Active region approximation OK` | PASS |
| Fixed bias switch + calculate | mode fixed; RB 1000 kΩ, RC 2.2 kΩ, β 100, VBE 0.7 | form shows RB and hides R1/R2/RE; `1.130` mA IC, `9.514` V VCE | RB shown, R1/R2/RE absent; `IC 1.130 mA`, `VC 9.514 V`, `VCE 9.514 V`, Active | PASS |
| Emitter bias switch + calculate | mode emitter; RB 1000 kΩ, RE 1 kΩ, RC 2.2 kΩ, β 100, VBE 0.7 | form shows RB/RE; `1.026` mA IC, `8.705` V VCE | RB/RE shown; `IC 1.026 mA`, `VC 8.705 V`, Active | PASS |
| DC SPICE smoke | reference values, analysis dc | real `.op` table, success status | VB 1.949 V, VE 1.289 V, VC 9.189 V, VCE 7.900 V, IC 1.278 mA; `run: success` | PASS |
| AC SPICE smoke | reference values, analysis ac | Bode SVG in scroll wrapper | one `.plot-scroll` SVG, one scroll hint, `run: success`; `-3 dB point: not determined in sweep range` | PASS |
| Transient SPICE smoke | reference values, analysis transient | time-domain SVG in scroll wrapper | one `.plot-scroll` SVG, one scroll hint, `run: success`; peak Vin 10.00 mV, peak Vout 17.51 mV | PASS |
| Invalid RE | RE 0 | browser blocks submission with numeric constraint | `validationMessage: Value must be greater than or equal to 0.000001.`; no new simulation submitted | PASS |

Full suite after the UI changes: `cmd /c ".venv\Scripts\python.exe -m unittest discover -s tests"` → `Ran 93 tests ... OK`.

### B1–B8 acceptance

All eight cases were executed on 24 Nov 2026 against the restarted Flask app at
<http://127.0.0.1:5000/>. Every case followed **Navigate → fresh DOM snapshot →
Select/Fill → Click the real submit button → Read the resulting DOM → Compare →
Screenshot**. No URL was typed as a substitute for a form submission, and no
result was inferred from a screenshot alone.

- **Tool actually used:** real headless Chrome 157.0.8103.80 driven over the
  Chrome DevTools Protocol WebSocket by a small stdlib Python client. The
  in-app browser returned `[browser.disconnected]` in this subagent session,
  and Playwright MCP is **not installed**; neither was used or claimed. Chrome
  network events confirmed `POST /simulate → HTTP 200` on port 5000.
- **Fresh server:** the old `app.py` processes were stopped and Flask was
  restarted with the repo venv (`serve5000.py`, `debug=False`,
  `use_reloader=False`). `GET /` returned HTTP 200 and the served HTML
  contained both `Lab 04` and `sim-grid`.
- **ngspice:** 47.x installed at
  `C:\Users\B6809737\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice.exe`.
  Windows `--version` switches are silent, so the version was confirmed by the
  installed 47.x path plus successful real `.op`, `.ac`, and `.tran` batch
  runs (engine `SimulationResult` objects were inspected directly).
- **Self-defined transistor model (not instructor-supplied):**
  `.model QNPN NPN(BF=100 IS=1e-14 VAF=100)`. The browser's provenance
  disclosure shows this exact netlist line alongside the ngspice log excerpt.
- **Reference circuit:** VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ,
  RL 10 kΩ, CIN = COUT = 10 µF, source 10 mV peak at 1 kHz. Resistors were
  submitted in kΩ, capacitors in µF, amplitude in mV and frequency in kHz;
  the engine converts these to Ω/F/V/Hz before building the netlist.

| Case | Method | Input | Expected / Reference | Observed (with units) | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B1 · Regression | Browser mode selector + `เปลี่ยนโหมด` + `Calculate DC Bias`; fresh DOM read after each real POST | Divider R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ; Fixed RB 1000 kΩ; Emitter RB 1000 kΩ, RE 1 kΩ; VCC 12 V, β 100, VBE 0.70 V | Divider IC 1.230 mA / VCE 8.052 V; Fixed IC 1.130 mA / VCE 9.514 V; Emitter IC 1.026 mA / VCE 8.705 V (Lab 03 references) | Divider IC **1.230 mA**, VCE **8.052 V**; Fixed IC **1.130 mA**, VCE **9.514 V**; Emitter IC **1.026 mA**, VCE **8.705 V**. Relevant fields changed per mode (Fixed: RB/RC only; Emitter: RB/RE/RC; Divider: R1/R2/RC/RE) | `docs/captures/acceptance/B1-divider-desktop-1280x900.png`; inline DOM observations in this row | PASS |
| B2 · DC SPICE | Browser `Run DC` on `/simulate` with reference circuit; compare DOM table with a fresh direct `run_simulation(SpiceParams, "dc")` and the ngspice log | Analysis `dc`; VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, RL 10 kΩ, CIN/COUT 10 µF, source 10 mV / 1 kHz | VB 1.949 V, VE 1.289 V, VC 9.189 V, VCE 7.900 V, IC 1.278 mA from ngspice `.op`; model QNPN; `run: success` | DOM: VB **1.949 V**, VE **1.289 V**, VC **9.189 V**, VCE **7.900 V**, IC **1.278 mA**; status `ngspice 47 · run: success`; source `QNPN NPN(BF=100 IS=1e-14 VAF=100)`, analysis `dc`. Engine summary: VB **1.949112 V**, VE **1.289454 V**, VC **9.189410 V**, VCE **7.899956 V**, IC **1.277541 mA** | `docs/captures/acceptance/B2-dc-desktop-1280x900.png`; log excerpt `ne 1.289454e+00`, `nc 9.189410e+00`, `nb 1.949112e+00`, `nvcc 1.200000e+01`; netlist and direct engine summary below | PASS |
| B3 · Change RE | Same DC form, only `sim_re` changed from 1 to 2 kΩ, then a second real `Run Simulation` | RE 1 kΩ → 2 kΩ; all other reference values unchanged | Operating point must change, not remain stale; fresh engine run must agree | Before VB **1.949 V**, VE **1.289 V**, VC **9.189 V**, IC **1.278 mA**; after VB **2.048 V**, VE **1.405 V**, VC **10.469 V**, VCE **9.065 V**, IC **0.696 mA**. Direct engine: VE **1.40455 V**, VC **10.46912 V**, IC **0.695855 mA** | `docs/captures/acceptance/B3-dc-re1k-before.png`, `B3-dc-re2k-after.png`; two HTTP 200 POSTs in browser network log | PASS |
| B4 · AC | Browser `.ac` run; read axes/labels and extract SVG polylines from the live DOM; independently re-run the engine on identical `SpiceParams` and compare every point | Reference circuit; `.ac dec 40 10 10Meg`, 10 mV peak source | Bode plot with frequency (Hz, 1e1–1e7), gain (dB), phase (deg); values from real ngspice sweep | One SVG, `viewBox 0 0 860 430`; axis labels `gain (dB)`, `phase (deg)`, `frequency (Hz)`; **241** gain points and **241** phase points; midband relative gain **+4.8598 dB**, phase at 1 kHz **−179.866°**, `-3 dB point: not determined in sweep range`. Point-by-point max deviation vs fresh engine rows: **0.005 px in x**, **≤0.00499 px in y** | `docs/captures/acceptance/B4-ac-desktop-1280x900.png`; numeric row and point comparison below | PASS |
| B5 · Transient | Browser `.tran` run; read time/voltage labels and SVG polylines; direct engine run for the same params; sign/correlation analysis of parsed rows | Reference circuit, 10 mV peak, 1 kHz; `.tran 0.01m 5m` | Vin and Vout versus time (ms, V); phase inversion; values from real ngspice run | One SVG with labels `time (ms)`, `Vin [V]`, `Vout [V]`, ticks 0/2.5/5 ms; **508** points per trace; DOM note `Peak Vin 10.00 mV, peak Vout 17.51 mV`. Parse: peak Vin **0.009998 V** at t **4.2528 ms**, Vout there **−0.017479 V**; Vin/Vout correlation over the last 1 ms = **−1.000** (inversion). Max deviation vs fresh engine rows: **≤0.00476 px in x**, **≤0.005 px in y** | `docs/captures/acceptance/B5-transient-desktop-1280x900.png`; selected parsed rows and comparison below | PASS |
| B6 · Change source | Browser transient run at 10 mV, then only `sim_amplitude` set to 20 mV and a second real run; compare DOM notes and polylines with two engine runs | Amplitude 10 → 20 mV peak; frequency fixed at 1 kHz | Waveform/peak must follow the source setting, not a hard-coded plot | DOM peaks **10.00 mV → 20.00 mV** Vin (**×2.000**) and **17.51 mV → 35.04 mV** Vout; engine peaks **0.009998 V → 0.019997 V** Vin and **0.017511 V → 0.035042 V** Vout. 20 mV SVG: **508** points per trace, max deviation **≤0.00476 px x / 0.005 px y** | `docs/captures/acceptance/B6-transient-10mV-before.png`, `B6-transient-20mV-after.png`; comparison below | PASS |
| B7 · Invalid / engine fail | (a) Set RE=0 in the real form and click Run; (b) second Flask on port 5001 with in-process `find_ngspice` monkeypatched to `None`, then a real browser run there | (a) RE = 0 kΩ, min constraint 0.000001; (b) reference DC run with engine discovery forced to fail | (a) native validation error and no new simulation; (b) explicit SPICE error, no result table, no `run: success` | (a) `validationMessage` exactly `Value must be greater than or equal to 0.000001.`, `checkValidity() = false`, **0** POSTs, result state stayed `idle`; (b) exact error text `การจำลอง SPICE ล้มเหลว: ngspice executable not found. Install ngspice 47 and add it to PATH.`; status `ngspice 47 · run: failed`, `data-sim-state=error`, **0** SPICE table rows, no `run: success`, real `POST /simulate` returned HTTP 200 | `docs/captures/acceptance/B7-re0-native-validation.png`, `B7-engine-unavailable-5001.png`; method and network log below | PASS |
| B8 · UI | Desktop 1280×900 and phone 390×844 emulation; mode switching then AC run and DOM overflow measurement at both sizes | Same reference inputs, analysis `ac`, mode switches Fixed → Divider | Graphs, units and buttons readable; no important content clipped | **Desktop:** buttons and units readable, plot visible; `innerWidth 1280 px`, `documentElement.scrollWidth 1280 px`, grid 1248 px, results 868 px, form 360 px, `.plot-scroll` clientWidth 818 px = SVG 818 px → PASS. **Phone (with result):** `innerWidth 390 px`, `documentElement.scrollWidth 390 px`, `bodyScrollWidth 390 px`; grid, results and form all 358 px; `.plot-scroll` clientWidth 308 px with internal `scrollWidth 640 px` (max scrollLeft 332 px); 640 px Bode SVG and both 241-point traces remain visible inside the scroller after `scrollLeft = 200 px`, and no element outside `.plot-scroll` extends past 390 px. Root page 390 px, not clipped | `docs/captures/acceptance/B8-desktop-1280x900.png`, `B8-mobile-390x844-root.png`, `B8-mobile-390x844.png`, `B8-mobile-390x844-full.png` (390 px wide), `B8-mobile-390x844-plot-scrolled.png` | **PASS** (desktop and phone; internal plot scroll is intended) |

#### B8 re-check after the fix

The first acceptance pass recorded B8 as FAIL: with an AC result at 390 px the
640 px `min-width` plot made the `1fr` grid track's automatic minimum 640 px,
expanding both cards to 690 px and the page to 706 px. The CSS was fixed inside
the existing `@media (max-width: 900px)` block (`grid-template-columns:
minmax(0, 1fr)` and `min-width: 0` on `.sim-grid > *`) with a regression test in
`tests/test_task4_ui.py`. B8 was then re-run end-to-end in the same real headless
Chrome/CDP setup (390×844, phone emulation, mode switches, reference AC run):
the measurements above replaced the failing ones and all B8 phone screenshots
were recaptured. No plot data or application code changed.

#### Provenance proof for the plotted data (B4, B5, B6)

For each plotted case the exact form values were converted to a
`SpiceParams(vcc_v=12, r1_ohm=100000, r2_ohm=22000, rc_ohm=2200,
re_ohm=1000, rl_ohm=10000, cin_f=1e-5, cout_f=1e-5, amplitude_v=0.01,
frequency_hz=1000)` (or `amplitude_v=0.02` for B6) and passed to
`spice_engine.run_simulation`. The returned `SimulationResult.ac` / `.tran`
lists were inspected, then converted with the plot's documented affine/log
mapping and compared with the `points` attribute of the `<polyline>` elements
read from the rendered `/simulate` DOM. Matching point counts plus sub-pixel
deviation (the SVG rounds coordinates to two decimals) proves the plotted
lines are the parsed ngspice rows, not source-code constants or a mock plot.

Selected AC rows from the fresh `run_simulation(..., "ac")` result:

| Frequency (Hz) | `gain_dbv` (dBV) | `phase_deg` (°) | Relative gain (dB, −20·log10(0.01 V) = +40 dB) |
| --- | --- | --- | --- |
| 10 | −35.2594 | −166.677 | +4.7406 |
| 1000 | −35.1402 | −179.866 | +4.8598 |
| 10000 | −35.1402 | −179.987 | +4.8598 |
| 10000000 | −35.1402 | −179.9998 | +4.8598 |

Selected transient rows from the fresh `run_simulation(..., "transient")`
result:

| Time (s) | Vin (V) | Vout (V) |
| --- | --- | --- |
| 0 | 0 | 0 |
| 0.0024728 | +0.001700719 | −0.00291846 |
| 0.0042528 | +0.009998452 | −0.0174789 |
| 0.0050000 | ≈ 0 (−1.22e−17) | −0.0000242388 |

| Comparison | Engine rows | SVG points | Max Δx (px) | Max Δy (px) |
| --- | --- | --- | --- | --- |
| B4 gain polyline | 241 | 241 | 0.005 | 0.00467 |
| B4 phase polyline | 241 | 241 | 0.005 | 0.00499 |
| B5 Vin polyline | 508 | 508 | 0.00476 | 0.00487 |
| B5 Vout polyline | 508 | 508 | 0.00476 | 0.005 |
| B6 Vin polyline at 20 mV | 508 | 508 | 0.00476 | 0.005 |
| B6 Vout polyline at 20 mV | 508 | 508 | 0.00476 | 0.005 |

The DC netlist used by the engine contains exactly
`.model QNPN NPN(BF=100 IS=1e-14 VAF=100)`, and its log excerpt contains the
`.op` node table `ne 1.289454e+00`, `nc 9.189410e+00`, `nb 1.949112e+00`,
`nvcc 1.200000e+01`, reproducing the displayed DC values.

#### Engine-failure method and exact evidence (B7)

A temporary script outside the repository imported the unchanged `app` module
and rebound both `app.find_ngspice` and `spice_engine.find_ngspice` to
`lambda: None`, then served the same application on port 5001 with
`debug=False, use_reloader=False`. No installed executable was renamed, moved
or modified; the normal server on port 5000 kept working with ngspice. The
browser navigated to `http://127.0.0.1:5001/`, filled the reference DC form and
clicked the real **Run Simulation** button. Chrome recorded
`POST http://127.0.0.1:5001/simulate → 200`. The rendered page showed the exact
error text above twice (form alert and results alert), the compact status
`ngspice 47 · run: failed`, `data-sim-state="error"`, no `.spice-table` rows and
no source line or `run: success` string. For the RE=0 sub-check the browser's
native constraint (`min="0.000001"`) stopped submission before any POST, so no
server-side RE=0 error was exercised; this is recorded as the native validation
path rather than an unobserved server error.

#### Limitations and NOT RUN

- The QNPN model is **self-defined** for this lab exercise; it is not an
  instructor-supplied or instructor-verified model. Results depend on its
  `BF=100`, `IS=1e-14`, `VAF=100` parameters.
- The Lab 03 analytical panel still uses the β/VBE forward-active
  approximation; it intentionally differs from SPICE (for example Divider
  IC 1.230 mA versus ngspice IC 1.278 mA).
- The AC sweep spans 10 Hz–10 MHz. The low-frequency −3 dB corner falls below
  the sweep start, so the UI correctly reports `-3 dB point: not determined in
  sweep range`; midband relative gain is about +4.86 dB (≈1.75 V/V).
- The transient plot is AC-coupled at the collector through COUT/RL; Vout is
  centred near 0 V and inverted relative to Vin. The phase-inversion statement
  is based on parsed row signs and a −1.000 correlation, not only on the image.
- **B8 mobile clipping resolved:** the earlier 706 px page width came from the
  `1fr` track's automatic minimum under the 640 px plot SVG. The mobile media
  query now uses `minmax(0, 1fr)` and `min-width: 0` on `.sim-grid > *`, so at
  390 px the page and cards are 390/358 px wide; the Bode plot scrolls *inside*
  its 308 px wrapper (640 px SVG) instead of overflowing the page. Intended
  internal scrolling remains; no important content is clipped.
- **NOT RUN:** no B1–B8 case was left unrun. The Task 4 Impeccable overlay
  attempt (recorded above) remains unavailable in this isolated session and is
  not part of the B1–B8 acceptance.

#### Capture index

`docs/captures/acceptance/` contains: `B1-divider-desktop-1280x900.png`,
`B2-dc-desktop-1280x900.png`, `B3-dc-re1k-before.png`, `B3-dc-re2k-after.png`,
`B4-ac-desktop-1280x900.png`, `B5-transient-desktop-1280x900.png`,
`B6-transient-10mV-before.png`, `B6-transient-20mV-after.png`,
`B7-re0-native-validation.png`, `B7-engine-unavailable-5001.png`,
`B8-desktop-1280x900.png`, `B8-desktop-1280x900-full.png`,
`B8-mobile-390x844-root.png`, `B8-mobile-390x844.png`,
`B8-mobile-390x844-full.png` (recaptured at 390 px after the fix), and
`B8-mobile-390x844-plot-scrolled.png` (Bode trace inside the horizontal
scroller).

Final full suite after the B8 fix and all acceptance work:
`cmd /c ".venv\Scripts\python.exe -m unittest discover -s tests"` →
`Ran 95 tests in 1.319s`, `OK`.
