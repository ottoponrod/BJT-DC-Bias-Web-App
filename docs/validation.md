# Validation — BJT DC Bias Web App (Lab 02)

## 1. ชุดทดสอบอ้างอิง

ค่าอุปกรณ์: VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ,
β = 100, VBE = 0.70 V

คำนวณด้วยมือ (Forward-Active):

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

ผลจากเว็บ (POST /calculate ด้วยค่าเดียวกัน) ตรงกับตารางข้างต้นที่ตำแหน่งทศนิยม 3 ตำแหน่ง
และถูกตรวจซ้ำโดย `tests/test_dc_bias.py::ActiveRegionTests::test_reference_values`

## 2. กรณีทดสอบอื่นที่ระบบรองรับ

| กรณี | เงื่อนไข | ผลที่คาดหวัง |
|---|---|---|
| Cutoff | VTH ≤ VBE | `region = cutoff`, IB = IC = IE = 0, VE = 0, VB = VTH, VC = VCE = VCC + warning |
| Saturation | VCE ≤ 0.3 V | `region = saturation` + warning ว่า Forward-Active ใช้ไม่ได้ |
| Near-saturation | 0.3 V < VCE < 1.0 V | `region = near-saturation` + warning ให้ตรวจสอบซ้ำ |
| ค่าผิด | R ≤ 0, β ≤ 0, VCC ≤ 0, VBE ≤ 0 หรือ VBE ≥ VCC | ข้อความ error ภาษาไทย, HTTP 200, หน้าเว็บไม่ล้ม |
| ข้อมูลไม่ครบ/ไม่ใช่ตัวเลข | ช่องว่าง หรือ `abc`, `1,000` | ข้อความ error ภาษาไทย, HTTP 200 |

## 3. ผลการทดสอบอัตโนมัติ

คำสั่ง: `python -m unittest discover -s tests -v`

```
Ran 24 tests in 0.016s

OK
```

- `tests/test_dc_bias.py` — 13 tests (ค่าอ้างอิง, validation, cutoff/saturation/near-saturation, boundary, ค่ามากผิดปกติ, NaN/∞)
- `tests/test_web.py` — 11 tests (GET ฟอร์ม, POST ผลลัพธ์, error cases, หน่วย Ω, stylesheet, warning)

## 4. ข้อจำกัดของแบบจำลอง

- ใช้ Forward-Active Approximation: β คงที่, VBE คงที่, ไม่คิด Early effect
- ไม่ใช่ ngspice/SPICE — ค่าที่ได้เป็นผลของสมการมือ ไม่ใช่ผลจำลองวงจรจริง
- เมื่อ VTH ≤ VBE (cutoff) หรือ VCE ≤ 0.3 V (saturation) แบบจำลองนี้ใช้ไม่ได้
  ระบบจะแสดง warning และ (ในกรณี cutoff) รายงานสภาวะ OFF ตามอุดมคติแทนค่าจากสมการ
