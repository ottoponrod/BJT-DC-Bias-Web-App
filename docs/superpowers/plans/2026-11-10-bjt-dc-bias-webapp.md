# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web Application หลายไฟล์ที่คำนวณ DC Operating Point ของวงจร BJT NPN Voltage-Divider Bias พร้อม validation, region warning และ automated tests ภายในขอบเขต Lab 02

**Architecture:** แยก engineering logic ไว้ใน `dc_bias.py` (ไม่ import Flask), Flask routes ใน `app.py` ทำหน้าที่ parse form → เรียก logic → render `templates/index.html`; CSS แยกใน `static/`; tests แยกเป็น unit tests ของสมการและ HTTP tests ผ่าน Flask test client

**Tech Stack:** Python 3.13, Flask 3.1.x, Jinja2, `unittest` (stdlib), HTML/CSS ล้วน (ไม่มี JavaScript)

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

## Global Constraints

- Python 3.13, Flask `>=3.0,<4.0`; ใช้ `unittest` เท่านั้น (ห้ามเพิ่ม pytest)
- โครงไฟล์: `app.py`, `dc_bias.py`, `templates/index.html`, `static/style.css`, `tests/test_dc_bias.py`, `tests/test_web.py`
- `dc_bias.py` ห้าม import Flask หรือรู้จัก HTML/HTTP
- หน่วย SI ภายในโมดูล: V และ Ω; กระแสเป็น A — แปลงหน่วยที่ `app.py`/template เท่านั้น
- หน่วยตัวต้านทานในฟอร์ม: dropdown `unit` ค่า `"kilo"` (ค่าเริ่มต้น) หรือ `"ohm"`, ใช้ร่วมกันทั้ง R1/R2/RC/RE; 1 kΩ = 1000 Ω
- สมการ: `VTH = VCC·R2/(R1+R2)`, `RTH = R1·R2/(R1+R2)`, `IB = (VTH−VBE)/(RTH+(β+1)·RE)`, `IC = β·IB`, `IE = (β+1)·IB`, `VE = IE·RE`, `VB = VE+VBE`, `VC = VCC−IC·RC`, `VCE = VC−VE`
- Region: `VTH ≤ VBE` → `"cutoff"`; `VCE ≤ 0.3` → `"saturation"`; `0.3 < VCE < 1.0` → `"near-saturation"`; อื่น ๆ → `"active"`
- ป้ายที่แสดงบนหน้าจอต้องเป็น `Active`, `Near-saturation`, `Saturation`, `Cutoff` (ตรงตัวอักษร เพื่อให้ web test ตรวจได้)
- Cutoff ต้องคืนสภาวะ OFF: `IB = IC = IE = 0`, `VE = 0`, `VB = VTH`, `VC = VCC`, `VCE = VCC` — ห้ามคืนกระแสติดลบ
- Validation แสดง error ด้วย HTTP **200** (ไม่ใช้ 400/500) และหน้าเว็บต้องไม่ล้ม
- ห้าม hard-code ผลลัพธ์ใน template; ทุกค่ามาจาก context
- ข้อความ UI เป็นภาษาไทย, ชื่อตัวแปร/ฟังก์ชันเป็นภาษาอังกฤษ
- คำสั่งรัน (ใช้ path ของ venv เพราะ `python` อาจยังไม่อยู่ใน PATH ของ process ที่รัน OpenCode):
  - tests: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
  - app: `.venv\Scripts\python.exe -m flask --app app run --debug` แล้วเปิด `http://127.0.0.1:5000/`
- **Commit ผ่าน GitHub Desktop เท่านั้น** (ผู้ใช้กดเอง): หลังจบแต่ละ Task ให้แจ้ง Summary ที่ต้องใช้ แล้วรอผู้ใช้ commit ก่อนเริ่ม Task ถัดไป
- ห้าม commit `.venv/`, `__pycache__/`, `.env`

## Review Focus

1. ผู้ใช้พิมพ์ตัวเลขที่มี comma หรือช่องว่าง เช่น `"1,000"` → ต้องได้ error ภาษาไทย ไม่ใช่ 500
2. `POST /calculate` ที่ไม่มี form data เลย (กดตรง ๆ) → ต้องคืน 200 พร้อม error
3. `VBE ≥ VCC` หรือ `VBE ≤ 0` → ต้องถูกปฏิเสธก่อนคำนวณ ไม่เกิดค่าติดลบ/หารศูนย์
4. `VTH` เท่ากับ `VBE` พอดี → ต้องจัดเป็น `cutoff` (ขอบเขต) ไม่ crash
5. ค่ามากผิดปกติ เช่น R = 1e9 Ω หรือ β = 1e6 → ต้องคำนวณได้ finite และ format ไม่พัง

---

### Task 1: Engineering core — dataclasses และการคำนวณ Active Region

**Files:**
- Create: `dc_bias.py`
- Create: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: ไม่มี
- Produces:
  - `class ValidationError(ValueError)`
  - `@dataclass(frozen=True) class BiasInputs` — ฟิลด์ `vcc, r1, r2, rc, re, beta, vbe` (float)
  - `@dataclass class BiasResult` — ฟิลด์ `vth, rth, ib, ic, ie, vb, ve, vc, vce` (float), `region: str`, `warnings: list[str]`
  - `def calculate_dc_bias(inputs: BiasInputs) -> BiasResult`

- [ ] **Step 1: เขียน failing test**

`tests/test_dc_bias.py`:

```python
import unittest

from dc_bias import BiasInputs, calculate_dc_bias

SAMPLE = dict(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
              re=1_000.0, beta=100.0, vbe=0.70)


class ActiveRegionTests(unittest.TestCase):
    def test_reference_values(self):
        result = calculate_dc_bias(BiasInputs(**SAMPLE))
        self.assertEqual(result.region, "active")
        self.assertAlmostEqual(result.vth, 2.1639, places=3)
        self.assertAlmostEqual(result.ib * 1e6, 12.2986, places=2)
        self.assertAlmostEqual(result.ic * 1e3, 1.2299, places=3)
        self.assertAlmostEqual(result.ie * 1e3, 1.2422, places=3)
        self.assertAlmostEqual(result.ve, 1.2422, places=3)
        self.assertAlmostEqual(result.vb, 1.9422, places=3)
        self.assertAlmostEqual(result.vc, 9.2943, places=3)
        self.assertAlmostEqual(result.vce, 8.0522, places=3)
```

- [ ] **Step 2: รันแล้วต้อง FAIL**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 3: สร้าง `dc_bias.py`**

ประกาศ `ValidationError`, `BiasInputs`, `BiasResult` ตาม Interfaces และ implement `calculate_dc_bias` ตามสมการใน Global Constraints โดยยังไม่ต้องมี validation/region ครบ (ให้ `region="active"`, `warnings=[]`) — body เขียนตามสมการตรง ๆ

- [ ] **Step 4: รันแล้วต้อง PASS**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `OK` และมี `test_reference_values ... ok`

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: add BJT DC bias calculation core`
Files: `dc_bias.py`, `tests/test_dc_bias.py`

---

### Task 2: Input validation

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `BiasInputs`, `ValidationError` จาก Task 1
- Produces: `calculate_dc_bias` โยน `ValidationError` เมื่อ input ไม่ถูกต้อง (ข้อความภาษาไทย)

- [ ] **Step 1: เขียน failing tests**

ต่อท้าย `tests/test_dc_bias.py`:

```python
class ValidationTests(unittest.TestCase):
    def assert_rejected(self, **overrides):
        with self.assertRaises(ValidationError):
            calculate_dc_bias(BiasInputs(**{**SAMPLE, **overrides}))

    def test_rejects_zero_or_negative_resistance(self):
        for field in ("r1", "r2", "rc", "re"):
            self.assert_rejected(**{field: 0.0})
            self.assert_rejected(**{field: -1.0})

    def test_rejects_nonpositive_beta(self):
        self.assert_rejected(beta=0.0)
        self.assert_rejected(beta=-50.0)

    def test_rejects_nonpositive_vcc(self):
        self.assert_rejected(vcc=0.0)
        self.assert_rejected(vcc=-12.0)

    def test_rejects_vbe_outside_range(self):
        self.assert_rejected(vbe=0.0)
        self.assert_rejected(vbe=-0.7)
        self.assert_rejected(vbe=12.0)
        self.assert_rejected(vbe=15.0)

    def test_error_message_is_thai_and_specific(self):
        with self.assertRaises(ValidationError) as ctx:
            calculate_dc_bias(BiasInputs(**{**SAMPLE, "r1": 0.0}))
        self.assertIn("ต้องมากกว่า 0", str(ctx.exception))
```

แก้ import ด้านบนเป็น:

```python
from dc_bias import BiasInputs, ValidationError, calculate_dc_bias
```

- [ ] **Step 2: รันแล้วต้อง FAIL**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL — `ValidationError` ยังไม่ถูกโยน (หรือ import ไม่ได้)

- [ ] **Step 3: เพิ่ม validation ใน `calculate_dc_bias`**

ก่อนคำนวณ ตรวจตามลำดับ: `vcc <= 0` → `"VCC ต้องมากกว่า 0"`; `r1/r2/rc/re <= 0` → `"ตัวต้านทานต้องมากกว่า 0 (R1, R2, RC, RE)"`; `beta <= 0` → `"β ต้องมากกว่า 0"`; `vbe <= 0` → `"VBE ต้องมากกว่า 0"`; `vbe >= vcc` → `"VBE ต้องน้อยกว่า VCC"` — โยน `ValidationError` ด้วยข้อความนั้น

- [ ] **Step 4: รันแล้วต้อง PASS**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `OK` (ทุก test ผ่าน)

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: validate DC bias inputs`

---

### Task 3: Operating-region detection (cutoff / saturation / near-saturation)

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `calculate_dc_bias` จาก Task 2
- Produces: `BiasResult.region` ∈ `{"active", "cutoff", "saturation", "near-saturation"}` และ `BiasResult.warnings` มีข้อความเมื่อไม่อยู่ใน active

- [ ] **Step 1: เขียน failing tests**

ต่อท้าย `tests/test_dc_bias.py`:

```python
class RegionTests(unittest.TestCase):
    def test_cutoff_returns_off_state(self):
        result = calculate_dc_bias(BiasInputs(
            vcc=5.0, r1=100_000.0, r2=10_000.0, rc=2_200.0,
            re=1_000.0, beta=100.0, vbe=0.70))
        self.assertEqual(result.region, "cutoff")
        self.assertEqual(result.ib, 0.0)
        self.assertEqual(result.ic, 0.0)
        self.assertEqual(result.ie, 0.0)
        self.assertAlmostEqual(result.ve, 0.0)
        self.assertAlmostEqual(result.vb, result.vth)
        self.assertAlmostEqual(result.vc, 5.0)
        self.assertAlmostEqual(result.vce, 5.0)
        self.assertTrue(result.warnings)

    def test_cutoff_boundary_vth_equals_vbe(self):
        vcc, r1, r2 = 7.0, 100_000.0, 10_000.0
        vth = vcc * r2 / (r1 + r2)
        result = calculate_dc_bias(BiasInputs(
            vcc=vcc, r1=r1, r2=r2, rc=2_200.0,
            re=1_000.0, beta=100.0, vbe=vth))
        self.assertEqual(result.region, "cutoff")

    def test_saturation_when_vce_negative_low(self):
        result = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
            re=100.0, beta=100.0, vbe=0.70))
        self.assertEqual(result.region, "saturation")
        self.assertTrue(result.warnings)

    def test_near_saturation_band(self):
        result = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_100.0,
            re=100.0, beta=100.0, vbe=0.70))
        self.assertEqual(result.region, "near-saturation")
        self.assertTrue(result.warnings)

    def test_active_has_no_warning(self):
        result = calculate_dc_bias(BiasInputs(**SAMPLE))
        self.assertEqual(result.warnings, [])

    def test_extreme_values_stay_finite(self):
        result = calculate_dc_bias(BiasInputs(
            vcc=1000.0, r1=1e9, r2=1e9, rc=1e9, re=1e9,
            beta=1e6, vbe=0.70))
        for value in (result.vth, result.rth, result.ib, result.ic, result.ie,
                      result.vb, result.ve, result.vc, result.vce):
            self.assertTrue(math.isfinite(value))
```

> เพิ่ม `import math` ที่หัวไฟล์ `tests/test_dc_bias.py`

- [ ] **Step 2: รันแล้วต้อง FAIL**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL — region ยังเป็น `"active"` ทุกกรณี

- [ ] **Step 3: เพิ่ม logic ใน `calculate_dc_bias`**

คำนวณ `vth`, `rth` ก่อน; ถ้า `vth <= vbe` → คืน `BiasResult` สภาวะ OFF ตาม Global Constraints พร้อม `region="cutoff"` และ warning ภาษาไทย ("วงจรอยู่ในสภาวะตัดขาด (cutoff): VTH ≤ VBE — แบบจำลอง Forward-Active ใช้ไม่ได้") แล้ว return ทันที; มิฉะนั้นคำนวณต่อและจัด region ตามเกณฑ์ พร้อมแนบ warning ที่ตรงกับ region (`saturation`: เตือน VCE ≤ 0.3 V, `near-saturation`: เตือน 0.3 < VCE < 1.0 V ใกล้ขอบอิ่มตัว)

- [ ] **Step 4: รันแล้วต้อง PASS**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `OK` (อย่างน้อย 10 tests)

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: detect cutoff and saturation regions`

---

### Task 4: Flask routes และ web tests

**Files:**
- Create: `app.py`
- Create: `templates/index.html` (โครงพื้นฐาน ยังไม่ตกแต่ง)
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `BiasInputs`, `ValidationError`, `calculate_dc_bias` จาก Task 3
- Produces:
  - `app: Flask` ระดับโมดูล
  - `GET /` → 200, ฟอร์มมี `name="vcc"` และ prefill ค่าตัวอย่าง
  - `POST /calculate` → 200, แสดงผลหรือ error
  - ฟอร์มใช้ field names: `vcc, r1, r2, rc, re, beta, vbe, unit`
  - template context: `form` (dict ของ raw string), `result` (BiasResult|None), `error` (str|None), `unit_label` (str)

- [ ] **Step 1: เขียน failing tests**

`tests/test_web.py`:

```python
import unittest

from app import app

VALID = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1",
         "beta": "100", "vbe": "0.7", "unit": "kilo"}


class WebTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_returns_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="vcc"', response.data)
        self.assertIn(b'name="unit"', response.data)

    def test_calculate_renders_results(self):
        response = self.client.post("/calculate", data=VALID)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.230", response.data)     # IC [mA]
        self.assertIn(b"8.052", response.data)     # VCE [V]
        self.assertIn("Active".encode(), response.data)

    def test_invalid_input_shows_error_not_crash(self):
        response = self.client.post("/calculate", data={**VALID, "r1": "0"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("ต้องมากกว่า 0".encode(), response.data)

    def test_missing_form_data_shows_error(self):
        response = self.client.post("/calculate", data={})
        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอก".encode(), response.data)

    def test_non_numeric_input_shows_error(self):
        response = self.client.post("/calculate", data={**VALID, "vcc": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("ตัวเลข".encode(), response.data)

    def test_comma_separated_input_shows_error(self):
        response = self.client.post("/calculate", data={**VALID, "r1": "1,000"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("ตัวเลข".encode(), response.data)
```

- [ ] **Step 2: รันแล้วต้อง FAIL**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: สร้าง `app.py` และ `templates/index.html`**

`app.py`: `app = Flask(__name__)`; route `GET /` ส่ง `form` เป็นค่าเริ่มต้น `{"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.70", "unit": "kilo"}`; route `POST /calculate` อ่าน `request.form` เป็น raw strings, ถ้าฟิลด์ใดว่าง → error `"กรุณากรอกข้อมูลให้ครบทุกช่อง"`, แปลง `float()` ใน try/except `ValueError` → error `"กรุณากรอกเป็นตัวเลข (ห้ามใช้ comma)"`, แปลงหน่วยด้วย `factor = 1000.0 if unit == "kilo" else 1.0`, เรียก `calculate_dc_bias`, จับ `ValidationError` → `error=str(exc)`; render `index.html` ด้วย `form` (raw), `result`, `error`, `unit_label` (`"kΩ"` หรือ `"Ω"`); ทุกกรณีคืน HTTP 200

`templates/index.html`: ฟอร์ม method post action `/calculate` มี input ครบ 8 ฟิลด์ (ใช้ `value="{{ form.vcc }}"` เป็นต้น), แสดง `error` ถ้ามี, แสดงตารางผล VB/VE/VC/VCE/IC พร้อมหน่วย และ region badge — ใช้ `{{ "%.3f"|format(result.ic * 1000) }}` สำหรับ IC [mA], `{{ "%.3f"|format(result.ib * 1e6) }}` สำหรับ IB [µA], `{{ "%.3f"|format(result.vb) }}` สำหรับแรงดัน

- [ ] **Step 4: รันแล้วต้อง PASS**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `OK` (16 tests ขึ้นไป)

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: add Flask routes and web tests`

---

### Task 5: Presentation — CSS และหน้าจอสมบูรณ์

**Files:**
- Create: `static/style.css`
- Modify: `templates/index.html`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: routes จาก Task 4
- Produces: หน้าเว็บที่ link `static/style.css`, แสดงผลครบตามหน่วย และแจ้ง warning ในหน้า

- [ ] **Step 1: เขียน failing test**

ต่อท้าย `tests/test_web.py`:

```python
    def test_page_links_stylesheet(self):
        response = self.client.get("/")
        self.assertIn(b"style.css", response.data)

    def test_results_show_units_and_warning(self):
        response = self.client.post("/calculate", data={**VALID, "re": "0.1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Saturation".encode(), response.data)
        self.assertIn("VCE".encode(), response.data)
        self.assertIn("mA".encode(), response.data)
```

- [ ] **Step 2: รันแล้วต้อง FAIL**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: FAIL — ยังไม่มี `style.css` ในหน้า

- [ ] **Step 3: สร้าง `static/style.css` และปรับ `index.html`**

`<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`; จัดหน้าเป็นการ์ด ฟอร์มซ้าย–ผลขวาบนจอใหญ่ และเรียงลงมาบนจอเล็ก; badge สี: Active เขียว, Near-saturation เหลือง, Saturation/Cutoff แดง; แสดง warning เป็นกล่องสีส้ม; คง `name` ของ field เดิมทั้งหมด

- [ ] **Step 4: รันแล้วต้อง PASS**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `OK`

- [ ] **Step 5: ตรวจด้วย Browser**

Run: `.venv\Scripts\python.exe -m flask --app app run --debug`
แล้วเปิด `http://127.0.0.1:5000/` — ตรวจด้วยตาว่า: ฟอร์ม prefill ครบ, กด Calculate ได้ผล 1.230 mA / 8.052 V / Active, ใส่ R1=0 แล้วเห็น error, เปลี่ยนหน่วยเป็น Ω แล้วผลยังถูกต้อง (ต้องกรอก 100000)

- [ ] **Step 6: Commit (GitHub Desktop)**

Summary: `feat: style DC bias interface`

---

### Task 6: เอกสารและตรวจรับขั้นสุดท้าย

**Files:**
- Modify: `README.md`
- Create: `docs/validation.md`

**Interfaces:**
- Consumes: แอปที่รันได้จาก Task 5
- Produces: หลักฐานตรวจรับ (ค่าอ้างอิง + ผล test) สำหรับส่ง Moodle

- [ ] **Step 1: อัปเดต `README.md`**

ระบุ: ต้องมี Python 3.10+, คำสั่ง `python -m venv .venv`, activate, `pip install -r requirements.txt`, `python -m flask --app app run --debug`, เปิด `http://127.0.0.1:5000/`, คำสั่งรัน tests, โครงสร้างไฟล์จริง และหมายเหตุว่าต้องรันผ่าน Flask ไม่ใช่เปิด `index.html` ตรง ๆ

- [ ] **Step 2: เขียน `docs/validation.md`**

ใส่: ตารางค่าอ้างอิงที่คำนวณมือของชุด VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70 (VB≈1.942, VE≈1.242, VC≈9.294, VCE≈8.052, IC≈1.230 mA), ผลรัน tests (คัดลอก output), และข้อจำกัดของแบบจำลอง Forward-Active (Cutoff/Saturation)

- [ ] **Step 3: รัน tests ครั้งสุดท้ายและบันทึกผล**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `OK` — คัดลอก output ลง `docs/validation.md`

- [ ] **Step 4: Commit (GitHub Desktop)**

Summary: `docs: add validation notes and README`

- [ ] **Step 5: Push และเก็บหลักฐาน**

GitHub Desktop → **Push origin** → คัดลอก commit SHA จากแท็บ History ไว้ส่ง Moodle พร้อมภาพหน้าจอผลคำนวณ
