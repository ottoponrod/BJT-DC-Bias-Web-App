"""DC bias calculations for a BJT common-emitter voltage-divider circuit.

This module is pure engineering logic: it knows nothing about Flask, HTTP or
HTML. All voltages are in volts, resistances in ohms and currents in amperes.
"""

from dataclasses import dataclass, field
import math


class ValidationError(ValueError):
    """Raised when the supplied component values cannot be used."""


@dataclass(frozen=True)
class BiasInputs:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


@dataclass
class BiasResult:
    vth: float
    rth: float
    ib: float
    ic: float
    ie: float
    vb: float
    ve: float
    vc: float
    vce: float
    region: str = "active"
    warnings: list[str] = field(default_factory=list)


def calculate_dc_bias(inputs: BiasInputs) -> BiasResult:
    """Return the DC operating point of a voltage-divider biased BJT."""
    if not all(math.isfinite(value) for value in (
        inputs.vcc, inputs.r1, inputs.r2, inputs.rc, inputs.re,
        inputs.beta, inputs.vbe,
    )):
        raise ValidationError("ค่าอินพุตต้องเป็นจำนวนจำกัด (ห้าม NaN หรือ ∞)")

    if inputs.vcc <= 0:
        raise ValidationError("VCC ต้องมากกว่า 0")
    if inputs.r1 <= 0 or inputs.r2 <= 0 or inputs.rc <= 0 or inputs.re <= 0:
        raise ValidationError("ตัวต้านทานต้องมากกว่า 0 (R1, R2, RC, RE)")
    if inputs.beta <= 0:
        raise ValidationError("β ต้องมากกว่า 0")
    if inputs.vbe <= 0:
        raise ValidationError("VBE ต้องมากกว่า 0")
    if inputs.vbe >= inputs.vcc:
        raise ValidationError("VBE ต้องน้อยกว่า VCC")

    vth = inputs.vcc * inputs.r2 / (inputs.r1 + inputs.r2)
    rth = inputs.r1 * inputs.r2 / (inputs.r1 + inputs.r2)

    if vth <= inputs.vbe:
        return BiasResult(
            vth=vth,
            rth=rth,
            ib=0.0,
            ic=0.0,
            ie=0.0,
            vb=vth,
            ve=0.0,
            vc=inputs.vcc,
            vce=inputs.vcc,
            region="cutoff",
            warnings=[
                "วงจรอยู่ในสภาวะตัดขาด (cutoff): VTH ≤ VBE — แบบจำลอง "
                "Forward-Active ใช้ไม่ได้ ค่าที่แสดงคือสภาวะ OFF ตามอุดมคติ"
            ],
        )

    ib = (vth - inputs.vbe) / (rth + (inputs.beta + 1) * inputs.re)
    ic = inputs.beta * ib
    ie = (inputs.beta + 1) * ib

    ve = ie * inputs.re
    vb = ve + inputs.vbe
    vc = inputs.vcc - ic * inputs.rc
    vce = vc - ve

    warnings: list[str] = []
    if vce <= 0.3:
        region = "saturation"
        warnings.append(
            "VCE ≤ 0.3 V: ทรานซิสเตอร์อยู่ในสภาวะอิ่มตัว (saturation) — "
            "แบบจำลอง Forward-Active ใช้ไม่ได้ ค่าที่ได้เป็นเพียงค่าประมาณ"
        )
    elif vce < 1.0:
        region = "near-saturation"
        warnings.append(
            "VCE ใกล้ขอบอิ่มตัว (0.3 V < VCE < 1.0 V) — "
            "ผลลัพธ์อาจคลาดเคลื่อนจากของจริง ควรตรวจสอบด้วยการจำลอง"
        )
    else:
        region = "active"

    return BiasResult(
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
    )
