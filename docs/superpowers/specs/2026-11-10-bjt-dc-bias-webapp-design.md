# Lab 02 — BJT DC Bias Web App · Design

**Date:** 2026-11-10
**Course:** ENG29 2121 Computer Programming for Electrical Engineers (2/2569)
**Repo:** `transistor-simulator`

## Intent and why

นักศึกษาต้องสร้าง Web Application จริง (ไม่ใช่ HTML ไฟล์เดียว) ที่คำนวณ DC Operating Point
ของวงจร BJT NPN Common-Emitter แบบ Voltage-Divider Bias เพื่อให้เห็นเส้นแบ่งระหว่าง
Frontend (ฟอร์ม/HTML), Backend (Flask route), Engineering Logic (สมการ Python) และ Tests
ภายในเวลาคาบเดียว (~3 ชั่วโมง)

ความสำเร็จที่ผู้ใช้ต้องการ: เปิดเว็บใน Browser ได้จริง กรอกค่าแล้วได้ผลที่ถูกต้องตามสมการ
พร้อมหน่วย มีการแจ้งข้อผิดพลาดและคำเตือนเมื่อแบบจำลองใช้ไม่ได้ และ commit ขึ้น GitHub ได้

## Goals

1. `GET /` แสดงฟอร์มกรอกค่า พร้อมค่าตัวอย่างเริ่มต้น (VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70)
2. `POST /calculate` รับค่า → เรียก Python คำนวณ → render ผลในหน้าเดิม พร้อมคงค่าที่กรอกไว้ (echo)
3. แสดง VB, VE, VC, VCE [V], IC [mA] และ IB, IE เพิ่มเติม พร้อมหน่วยกำกับ
4. Validation: ข้อมูลหาย/ไม่ใช่ตัวเลข, R≤0, β≤0, VCC≤0, VBE≤0 หรือ VBE≥VCC → ข้อความ error ที่อ่านรู้เรื่อง, HTTP ยังเป็น 200 และหน้าเว็บไม่ล้ม
5. Region warning: Cutoff (VTH ≤ VBE), Saturation (VCE ≤ 0.3 V), Near-saturation (0.3 < VCE < 1.0 V) — แสดงข้อความว่า Forward-Active approximation ใช้ไม่ได้/ควรระวัง
6. Automated tests: ≥3 unit tests ของสมการ + ≥1 Flask test client test
7. รันได้ตาม README และ commit/push ผ่าน GitHub Desktop

## Non-goals

- AC small-signal, Bode plot, transient, signal generator, overlay animation
- Bias template อื่น (Fixed bias, Emitter bias) — สัปดาห์ถัดไป
- SPICE/ngspice, DC load line, FET
- ระบบ login, ฐานข้อมูล, deployment, JavaScript framework, build tool
- การวาดวงจรแบบ interactive (รูป/ไดอะแกรมคงที่พอ)

## Constraints

- Python 3.13 (ติดตั้งแล้ว), Flask 3.1.x, `unittest` จาก stdlib เท่านั้น (ไม่เพิ่ม pytest)
- โครงหลายไฟล์: `app.py`, `dc_bias.py`, `templates/index.html`, `static/style.css`, `tests/`
- `dc_bias.py` ต้องไม่ import Flask และไม่รู้จัก HTML/HTTP
- เปิดที่ `http://127.0.0.1:5000/` เท่านั้น (ไม่ใช่ `file://`)
- ห้าม commit `.venv/`, `__pycache__/`, `.env`
- งานต้องจบในคาบ — เลือกความเรียบง่ายเมื่อมีทางเลือก

## Approaches considered

**ก. Route เดียว `GET/POST /`** — โค้ดน้อยสุด แต่ template จะมีเงื่อนไขเยอะ และแยกทดสอบหน้าฟอร์มกับหน้าผลได้ไม่ชัด

**ข. แยก `GET /` และ `POST /calculate` (เลือกใช้)** — ตรงกับเกณฑ์ A2 ของ handout, ความรับผิดชอบชัด, เขียน HTTP test ได้ตรง ๆ, ต่อยอด Bias Template ได้ง่าย แลกกับ route/partial เพิ่มเล็กน้อย

**ค. JSON API + JavaScript** — UI ลื่นและนำ API ไปใช้ต่อได้ แต่ต้องเขียน JS และมีตรรกะแสดงผลซ้ำสองที่ เสี่ยงเบี่ยงจากเป้าหมายการเรียนรู้ และกินเวลา

**เหตุผลที่เลือก ข.:** ผู้ใช้มอบการตัดสินใจให้ผู้พัฒนาเลือก — เลือก ข. เพราะยังเห็นชัดว่า Python เป็นผู้คำนวณและส่ง HTML กลับมา, ผ่านเกณฑ์ตรวจรับตรง ๆ, และเหลือเวลาไปลงกับ validation/warning/tests

## Decisions (as decided)

### หน่วยของตัวต้านทาน
- ฟอร์มมี dropdown หน่วย **Ω / kΩ** ใช้ร่วมกันทั้ง 4 ตัวต้านทาน (R1, R2, RC, RE) ค่าเริ่มต้น **kΩ**
- แปลงเป็น Ω จุดเดียวใน `app.py` ก่อนส่งเข้า `dc_bias.py` (1 kΩ = 1000 Ω)
- แสดงหน่วยที่ผู้ใช้เลือกกำกับใน label ของผลลัพธ์/ฟอร์ม เพื่อไม่ให้สับสน

### สมการ (Forward-Active, β และ VBE คงที่)
```
VTH = VCC·R2/(R1+R2)
RTH = R1·R2/(R1+R2)
IB  = (VTH−VBE)/(RTH+(β+1)·RE)
IC  = β·IB
IE  = (β+1)·IB
VE  = IE·RE
VB  = VE+VBE
VC  = VCC−IC·RC
VCE = VC−VE
```

### ค่าอ้างอิงสำหรับทดสอบ
VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V
→ VTH≈2.1639 V, RTH≈18.033 kΩ, IB≈12.298 µA, IC≈1.2298 mA, IE≈1.2421 mA,
VE≈1.2421 V, VB≈1.9421 V, VC≈9.2944 V, VCE≈8.0523 V (Active)

### โครง API ภายใน
- `dc_bias.py`:
  - `@dataclass BiasInputs`: vcc, r1, r2, rc, re, beta, vbe (ทั้งหมดเป็น float, หน่วย SI: V, Ω)
  - `@dataclass BiasResult`: vth, rth, ib, ic, ie, vb, ve, vc, vce, region, warnings
  - `class ValidationError(ValueError)` — ข้อความภาษาไทยที่แสดงต่อผู้ใช้ได้
  - `def calculate_dc_bias(inputs: BiasInputs) -> BiasResult` — ตรวจความถูกต้องแล้วคำนวณ
  - `region` เป็นหนึ่งใน `"active" | "cutoff" | "saturation" | "near-saturation"`
  - กรณี VTH ≤ VBE (`cutoff`) ให้คืนค่าสภาวะ OFF โดยตรง: IB = IC = IE = 0, VE = 0, VB = VTH, VC = VCC, VCE = VCC — ห้ามคืนกระแสติดลบ และไม่คำนวณ VC จากสมการ Forward-Active
- `app.py`:
  - `GET /` → `render_template("index.html", form=defaults)`
  - `POST /calculate` → parse form → `BiasInputs` → `calculate_dc_bias` → render `index.html` ด้วย `result` และค่า form เดิม
  - จับ `ValidationError` → render `index.html` ด้วย `error` (HTTP 200)
  - จับ `ValueError` จาก `float()` → error "กรุณากรอกเป็นตัวเลข"
  - `app = Flask(__name__)` ระดับโมดูล เพื่อให้ `flask --app app run` และ test client ใช้ได้

### กติกาการแสดงผล
- ค่าแรงดันทศนิยม 3 ตำแหน่ง (V), กระแส mA 3 ตำแหน่ง, IB แสดงเป็น µA
- Region แสดงเป็น badge: Active (เขียว), Near-saturation (เหลือง), Saturation (แดง), Cutoff (แดง)
- Cutoff (VTH ≤ VBE): **ไม่รายงานค่าจากสมการ Forward-Active** แต่แสดง "สภาวะ OFF" ตามอุดมคติ คือ IB = IC = IE = 0, VE = 0, VB = VTH, VC = VCC, VCE = VCC พร้อม warning ว่าแบบจำลอง Forward-Active ใช้ไม่ได้และค่าที่แสดงคือสภาวะตัดขาด
- Saturation: เตือนว่า VCE ต่ำกว่า 0.3 V แบบจำลอง Forward-Active ใช้ไม่ได้ ค่าที่ได้เป็นเพียงค่าประมาณ
- ห้ามแสดงตัวเลขใด ๆ ที่ hard-code ไว้ใน template — ทุกค่าต้องมาจาก context

### Tests
- `tests/test_dc_bias.py`
  - ค่าอ้างอิงชุดตัวอย่าง → ตรวจ VB, VE, VC, VCE, IC ด้วย `assertAlmostEqual` (tolerance 1e-3 V / 1e-6 A ตามเหมาะสม)
  - R=0 / R ติดลบ / β≤0 / VCC≤0 → `ValidationError`
  - VTH ≤ VBE → region `cutoff` และ IB = IC = IE = 0, VE = 0, VB ≈ VTH, VC ≈ VCC, VCE ≈ VCC (ไม่มีค่าติดลบ)
  - VCE ≤ 0.3 V (เช่น RC ใหญ่/RE เล็ก) → region `saturation`
- `tests/test_web.py`
  - `GET /` → 200 และมี `name="vcc"` ใน HTML
  - `POST /calculate` ค่าถูกต้อง → 200 และมี `1.230` (IC) ใน response
  - `POST /calculate` ค่าผิด (R1=0) → 200 และมีข้อความ error

## Build plan outline (สำหรับขั้น writing-plans)

1. `dc_bias.py` + unit tests (TDD)
2. `app.py` routes + web tests
3. `templates/index.html` + `static/style.css`
4. README ปรับให้ตรงกับของจริง + ตรวจรันจริงใน browser
5. Commit ผ่าน GitHub Desktop

## Left to the builder

- การจัดหน้าตา/สี/ระยะห่างของ CSS และการวาง layout (ฟอร์มซ้าย–ผลขวา หรือเรียงลงมา)
- ถ้อยคำภาษาไทยของ label/ข้อความ warning ทั้งหมด (ต้องอ่านรู้เรื่องและตรงความหมาย)
- การเลือก tolerance ของ `assertAlmostEqual`
- การแบ่ง partial template (ถ้าต้องการ) — ไม่บังคับ
