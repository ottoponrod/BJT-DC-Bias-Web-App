# transistor-simulator

Lab 03 — ENG29 2121 (2/2569): Flask Web Application สำหรับคำนวณ **BJT DC Bias**
วงจร NPN Common-Emitter 3 โหมด

- **Voltage Divider Bias** (ต่อยอดจาก Lab 02)
- **Fixed Bias** — RB จาก VCC ไป Base, Emitter ต่อลงกราวด์
- **Emitter Bias (แหล่งจ่ายเดียว)** — RB จาก VCC ไป Base, RE จาก Emitter ลงกราวด์

## GitHub / Commit

- Repository: <https://github.com/ottoponrod/BJT-DC-Bias-Web-App>
- Commit SHA: `50e94c456da9f943a8168579697cd1107f627d05` (commit ที่เพิ่มแผนภาพ
  วงจรครบทั้ง 3 โหมด; งานโหมด Fixed/Emitter, เทสต์, หลักฐาน A1–A5 และเอกสาร
  ชุดนี้อยู่ใน `24f157f079127c860e21d92818c164fdaf9b7762`)

## ความต้องการของระบบ

- Python 3.10 ขึ้นไป (พัฒนาและทดสอบด้วย Python 3.13)
- Flask 3.x (`requirements.txt`)
- Git และ GitHub Desktop (สำหรับ commit/push)

## การติดตั้งและรัน

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run
```

เปิด <http://127.0.0.1:5000/> ใน Browser

> ต้องรันผ่าน Flask Server เท่านั้น การ double-click เปิด `templates/index.html`
> จะไม่ได้ผลลัพธ์ เพราะโปรแกรมคำนวณอยู่ใน Python Backend

## วิธีใช้

1. เลือก **โหมดไบอัส** จาก dropdown (Divider / Fixed / Emitter)
2. กด **เปลี่ยนโหมด** เพื่อให้ฟอร์มแสดงช่องของโหมดนั้น
   (ปุ่มนี้ใช้ `formnovalidate` จึงสลับโหมดได้แม้ยังกรอกไม่ครบ)
3. กรอกค่าอุปกรณ์ เลือกหน่วยตัวต้านทาน (kΩ หรือ Ω) แล้วกด **Calculate DC Bias**
4. อ่านผล VB, VE, VC, VCE [V] และ IC [mA], IB [µA], IE [mA] พร้อมสถานะการทำงาน

| โหมด | ช่องตัวต้านทานที่ใช้ |
|---|---|
| Voltage Divider | R1, R2, RC, RE |
| Fixed | RB, RC |
| Emitter | RB, RE, RC |

ทุกโหมดใช้ VCC, β และ VBE ร่วมกัน และแปลงหน่วยที่จุดรับข้อมูลครั้งเดียว
(เช่น 1 MΩ กรอกเป็น `1000` kΩ หรือ `1000000` Ω)

## การทดสอบ

```powershell
python -m unittest discover -s tests -v
```

ผลปัจจุบัน: **50 tests OK** (22 สมการ + 28 Flask)

## โครงสร้างไฟล์

```
transistor-simulator/
├── app.py                  # Flask routes: GET / และ POST /calculate + mode dispatch
├── dc_bias.py              # สมการ 3 โหมด + validation + region detection
├── templates/index.html    # ฟอร์มตามโหมด + แผนภาพ SVG ครบ 3 โหมด + ตารางผลลัพธ์
├── static/style.css        # การจัดหน้าและ responsive layout
├── static/app.js           # live label บนแผนภาพวงจร
├── tests/test_dc_bias.py   # unit tests ของสมการ (22 tests)
├── tests/test_web.py       # Flask test client (28 tests)
├── requirements.txt
└── docs/
    ├── validation.md       # ค่าอ้างอิง, ตาราง A1–A5, ผลทดสอบ
    └── evidence/lab03/     # screenshot A1–A5 + ภาพแผนภาพวงจร 3 โหมด
```

## ค่าอินพุตและผลลัพธ์

- อินพุต: `VCC` [V], ตัวต้านทานตามโหมด (เลือกหน่วย Ω หรือ kΩ), `β`, `VBE` [V]
- เอาต์พุต: `VB`, `VE`, `VC`, `VCE` [V], `IC` [mA], `IB` [µA], `IE` [mA]
  และสถานะการทำงาน
- สถานะ: `Active`, `Near-saturation` (0.3 V < VCE < 1.0 V),
  `Saturation` (VCE ≤ 0.3 V), `Cutoff` (ไบอัสไม่พอ)

## สมการที่ใช้ (Forward-Active Approximation)

```
Fixed      IB = (VCC − VBE) / RB
Emitter    IB = (VCC − VBE) / [RB + (β+1)RE]
Divider    IB = (VTH − VBE) / [RTH + (β+1)RE]
           VTH = VCC·R2/(R1+R2)      RTH = R1·R2/(R1+R2)

IC  = β·IB      IE = (β+1)·IB
VE  = IE·RE (Emitter/Divider) หรือ 0 V (Fixed)
VB  = VE+VBE    VC = VCC−IC·RC      VCE = VC−VE
```

## AI ทำอะไร / นักศึกษาตรวจอะไร

**AI (OpenCode + Superpowers) ทำ:**

- อ่านโค้ด Lab 02 เดิมและวางแผนต่อยอดโดยไม่สร้างโปรเจกต์ใหม่
- เพิ่ม `calculate_fixed_bias()` และ `calculate_emitter_bias()` ใน `dc_bias.py`
  พร้อม validation และการแบ่ง region แบบเดียวกับ Divider
- เพิ่ม mode dispatch, การแปลงหน่วย และการตรวจเฉพาะช่องของแต่ละโหมดใน `app.py`
- เพิ่ม dropdown โหมด, ช่องอินพุตแบบมีเงื่อนไข และปุ่มเปลี่ยนโหมดในเทมเพลต
- วาดแผนภาพวงจร SVG ให้ครบทั้ง 3 โหมด (Divider/Fixed/Emitter) พร้อม label ค่าแบบ live
- เขียนเทสต์ใหม่ก่อนแก้โค้ด (TDD) และรันเทสต์จนผ่านทั้งหมด 50 tests
- เปิดเว็บด้วย OpenCode Browser ตรวจ A1–A5 และบันทึก screenshot เป็นหลักฐาน
- อัปเดต `docs/validation.md` และ README นี้

**นักศึกษาตรวจเอง:**

- ตรวจสมการทั้งสามโหมดกับความรู้ Engineering Electronics
  (IB, IC, IE, VE, VB, VC, VCE และเงื่อนไข cutoff/saturation)
- ตรวจหน่วยว่า kΩ ถูกคูณ 1000 เป็น Ω ก่อนเข้าฟังก์ชัน
- คำนวณมือกรณี A2 (Fixed, RB = 1 MΩ) และ A3/A4 (Emitter) เทียบกับผลบนเว็บ
  → ตรงกันที่ทศนิยม 3 ตำแหน่ง
- ทำนายผล A4 ก่อนรันว่า IC จะลดลงเมื่อ RE เพิ่ม และตรวจว่าผลจริงลดลงจริง
- ตรวจว่าโหมด Fixed ไม่มีช่อง RE, โหมด Emitter มี RB+RE และปุ่มเปลี่ยนโหมด
  ใช้งานได้แม้ฟอร์มยังกรอกไม่ครบ
- ตรวจข้อความ error กรณี RB = 0 ว่าเป็นภาษาไทยและไม่มีผลรอบก่อนค้างอยู่
- เปิดดูโค้ดที่ AI เปลี่ยน (`git diff`) และรันเทสต์ซ้ำด้วยคำสั่งใน README

## หลักฐานผลตรวจ A1–A5

ตารางผลและค่าอ้างอิงโดยละเอียดอยู่ใน [`docs/validation.md`](docs/validation.md)
รูปหลักฐานจากเบราว์เซอร์จริงอยู่ใน [`docs/evidence/lab03/`](docs/evidence/lab03/)

| # | กรณี | IC (mA) | VCE (V) |
|---|---|---|---|
| A1 | Divider (Lab 02 เดิม) | 1.230 | 8.052 |
| A2 | Fixed, RB = 1 MΩ | 1.130 | 9.514 |
| A3 | Emitter, RE = 1 kΩ | 1.026 | 8.705 |
| A4 | Emitter, RE = 2 kΩ | 0.940 | 8.033 |
| A5 | Fixed, RB = 0 | error: `RB ต้องมากกว่า 0 Ω` | — |

## ขอบเขต (Week 3)

DC Bias เท่านั้น — ไม่มี AC, Transient, Bode Plot, Signal Generator, SPICE
หรือ Overlay Animation

## Lab 04 — CE Amplifier Simulator (SPICE จริง)

ส่วนนี้ต่อยอดจาก Lab 03 โดยเพิ่ม route `/simulate` ที่เรียก **ngspice 47**
จริง ไม่ได้แก้สมการ `/calculate` หรือ `dc_bias.py` ของ Lab 03

### ติดตั้ง ngspice (Windows)

1. ดาวน์โหลด ngspice 47 (Windows 64-bit) จากหน้า release ทางการของ
   ngspice/SourceForge แล้วแตกไฟล์ เช่น `%LOCALAPPDATA%\Programs\ngspice-47`
2. เพิ่มโฟลเดอร์ `<install>\Spice64\bin` ลงใน PATH ของผู้ใช้
   (System Properties → Environment Variables → User `Path` → Edit หรือ
   `setx PATH "%PATH%;<install>\Spice64\bin"` แล้วเปิด terminal ใหม่)
3. ตรวจสอบด้วย `where ngspice` และรัน netlist จริง 1 ไฟล์
   (`ngspice -b -o result.log circuit.cir`) — บน Windows `--version` ไม่พิมพ์
   ข้อความ จึงยืนยันเวอร์ชันด้วยโฟลเดอร์ 47.x และผลรัน `.op` / `.ac` / `.tran`
4. แอปมี fallback ไปที่
   `C:\Users\B6809737\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice.exe`
   กรณี PATH ไม่เห็น ngspice ตอนเปิด Flask จาก GUI

### ติดตั้ง dependencies และรันเซิร์ฟเวอร์

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

เปิด <http://127.0.0.1:5000/> ในเบราว์เซอร์ (ต้องรันผ่าน Flask เสมอ
ห้าม double-click `templates/index.html`) ถ้าแก้ template ขณะเซิร์ฟเวอร์รัน
ให้ restart Flask เพราะ Jinja cache template ไว้ใน process

### Reproduce 1 run (DC / AC / transient)

ในหน้า **Lab 04: BJT CE Amplifier Simulator** กรอกค่าอ้างอิง
VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, RL 10 kΩ,
CIN = COUT = 10 µF, Amplitude 10 mV peak, Frequency 1 kHz, units = kΩ
เลือก `DC operating point (.op)` / `Frequency response (.ac)` /
`Time domain (.tran)` แล้วกด **Run Simulation**

- DC: ควรเห็น VB 1.949 V, VE 1.289 V, VC 9.189 V, VCE 7.900 V, IC 1.278 mA
- AC: ควรเห็น Bode plot (gain dB / phase deg / frequency Hz) และ
  `run: success`; gain กลางช่วงประมาณ +4.86 dB
- Transient: ควรเห็น Vin/Vout vs time พร้อม Peak Vin 10.00 mV,
  Peak Vout 17.51 mV และสัญญาณ Vout กลับเฟสกับ Vin

เรียก engine โดยตรงจาก root ของ repo ได้ด้วย venv Python:

```python
from spice_engine import SpiceParams, run_simulation

p = SpiceParams(12, 100_000, 22_000, 2_200, 1_000, 10_000,
                10e-6, 10e-6, 0.010, 1_000)
for analysis in ("dc", "ac", "transient"):
    print(analysis, run_simulation(p, analysis).summary)
```

โมเดลที่ใช้คือ `.model QNPN NPN(BF=100 IS=1e-14 VAF=100)` ซึ่งเป็น
**self-defined reference model** ไม่ใช่โมเดลที่อาจารย์จัดให้ ผลตรวจ
B1–B8, หลักฐานรูปภาพ และข้อจำกัดอยู่ใน [`docs/validation.md`](docs/validation.md)
และ [`docs/captures/acceptance/`](docs/captures/acceptance/)
(ชุดทดสอบปัจจุบัน: 94 tests OK)

### AI ทำอะไร / นักศึกษาตรวจอะไร (Lab 04)

**AI ทำ:** เพิ่ม `spice_engine.py` (netlist, runner, parser), route `/simulate`,
SVG plot ที่สร้างจาก row ของ ngspice และ UI สำหรับ DC/AC/transient;
เขียนเทสต์และบันทึกหลักฐาน B1–B8 ลงใน docs พร้อม captions

**AI ทำ:** ทดสอบการเปลี่ยน RE, การเปลี่ยน amplitude, RE=0 และกรณีหา engine
ไม่เจอ bằng Flask อีก process บน port 5001 (monkeypatch เฉพาะ in-process)

**นักศึกษาตรวจ:** รัน ngspice ด้วย netlist ที่โชว์ในหน้า results แล้วเทียบ
ค่าตาราง `.op` และกราฟกับ log ที่ได้จริง อย่าเชื่อ screenshot เพียงอย่างเดียว

**นักศึกษาตรวจ:** คำนวณ gain กลางช่วงจาก `20·log10(Vout/Vin)` และอธิบาย
ว่าทำไม Vout กลับเฟส 180° และทำไม `-3 dB` ไม่อยู่ในช่วง sweep 10 Hz–10 MHz

**นักศึกษาตรวจ:** ดู `git diff` และรันชุดเทสต์ซ้ำ รวมถึงเปิดหน้า 390 px
หลังรัน AC เพื่อยืนยันข้อบกพร่อง clipping ที่บันทึกไว้ในตาราง B8
