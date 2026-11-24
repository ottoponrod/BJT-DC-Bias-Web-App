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

Full browser acceptance evidence is recorded after Task 5.
