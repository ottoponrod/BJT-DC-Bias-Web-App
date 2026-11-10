# transistor-simulator

Lab 02 — ENG29 2121 (2/2569): Flask Web Application สำหรับคำนวณ **BJT DC Bias**
วงจร NPN Common-Emitter แบบ Voltage-Divider Bias

## ความต้องการของระบบ

- Python 3.10 ขึ้นไป (พัฒนาและทดสอบด้วย Python 3.13)
- Flask 3.x (`requirements.txt`)
- Git และ GitHub Desktop (สำหรับ commit/push)

## การติดตั้งและรัน

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

เปิด <http://127.0.0.1:5000/> ใน Browser

> ต้องรันผ่าน Flask Server เท่านั้น การ double-click เปิด `templates/index.html`
> จะไม่ได้ผลลัพธ์ เพราะโปรแกรมคำนวณอยู่ใน Python Backend

## การทดสอบ

```powershell
python -m unittest discover -s tests -v
```

## โครงสร้างไฟล์

```
transistor-simulator/
├── app.py                  # Flask routes: GET / และ POST /calculate
├── dc_bias.py              # สมการ DC Bias + validation + region detection
├── templates/index.html    # ฟอร์มและตารางผลลัพธ์ (Jinja)
├── static/style.css        # การจัดหน้าและ responsive layout
├── tests/test_dc_bias.py   # unit tests ของสมการ (13 tests)
├── tests/test_web.py       # Flask test client (11 tests)
├── requirements.txt
└── docs/
    ├── superpowers/        # design doc และ implementation plan
    └── validation.md       # ค่าอ้างอิงและผลการทดสอบ
```

## ค่าอินพุตและผลลัพธ์

- อินพุต: `VCC` [V], `R1`, `R2`, `RC`, `RE` (เลือกหน่วย Ω หรือ kΩ), `β`, `VBE` [V]
- เอาต์พุต: `VB`, `VE`, `VC`, `VCE` [V], `IC` [mA], `IB` [µA], `IE` [mA] และสถานะการทำงาน
- สถานะ: `Active`, `Near-saturation` (0.3 V < VCE < 1.0 V), `Saturation` (VCE ≤ 0.3 V), `Cutoff` (VTH ≤ VBE)

## สมการที่ใช้ (Forward-Active Approximation)

```
VTH = VCC·R2/(R1+R2)      RTH = R1·R2/(R1+R2)
IB  = (VTH−VBE)/(RTH+(β+1)RE)
IC  = β·IB      IE = (β+1)·IB
VE  = IE·RE     VB = VE+VBE
VC  = VCC−IC·RC   VCE = VC−VE
```

## ขอบเขต (Week 2)

DC Bias เท่านั้น — ไม่มี AC, Transient, Bode Plot, Signal Generator, SPICE หรือ Overlay Animation
