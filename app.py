"""Flask application for the BJT bias calculator and CE simulator.

Routes:
  GET  /           -> input forms (analytic bias + SPICE simulation)
  POST /calculate  -> validate input, pick the model from ``mode`` and render
                      the results. ``action=change_mode`` only reloads the
                      form for the chosen mode (it never calculates).
  POST /simulate   -> validate SPICE inputs, run real ngspice and render only
                      the parsed results, or an explicit error state.
"""

import math

from flask import Flask, render_template, request

from plots import bode_svg, transient_svg
from spice_engine import (
    ANALYSES,
    MODEL_NAME,
    SpiceError,
    SpiceParams,
    find_ngspice,
    run_simulation,
)

from dc_bias import (
    MODE_DIVIDER,
    MODE_EMITTER,
    MODE_FIXED,
    MODES,
    BiasInputs,
    ValidationError,
    calculate_dc_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
)

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rb": "1000",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
    "unit": "kilo",
}

NUMERIC_FIELDS = ("vcc", "r1", "r2", "rb", "rc", "re", "beta", "vbe")
RESISTOR_FIELDS = ("r1", "r2", "rb", "rc", "re")

# Which resistor inputs each mode actually uses.
MODE_FIELDS = {
    MODE_DIVIDER: ("r1", "r2", "rc", "re"),
    MODE_FIXED: ("rb", "rc"),
    MODE_EMITTER: ("rb", "re", "rc"),
}

MODE_LABELS = {
    MODE_DIVIDER: "Voltage Divider Bias",
    MODE_FIXED: "Fixed Bias",
    MODE_EMITTER: "Emitter Bias (แหล่งจ่ายเดียว)",
}

# Resistors default to kΩ; capacitors to µF, source to mV, frequency to kHz.
SIM_DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "rl": "10",
    "cin": "10",
    "cout": "10",
    "amplitude": "10",
    "frequency": "1",
    "sim_unit": "kilo",
    "analysis": "dc",
}
SIM_PARAM_FIELDS = (
    "vcc", "r1", "r2", "rc", "re", "rl", "cin", "cout",
    "amplitude", "frequency",
)
SIM_RESISTORS = ("r1", "r2", "rc", "re", "rl")
SIM_ANALYSIS_LABELS = {
    "dc": "DC operating point (.op)",
    "ac": "Frequency response (.ac)",
    "transient": "Time domain (.tran)",
}


def _unit_label(unit: str) -> str:
    return "kΩ" if unit == "kilo" else "Ω"


def _engine_status(state="not started"):
    located = "found" if find_ngspice() else "missing"
    return (
        f"ngspice 47 | engine: {located} | "
        f"model: {MODEL_NAME} NPN(BF=100 IS=1e-14 VAF=100) | run: {state}"
    )


def _render(
    form, mode, result=None, error=None, *,
    sim_form=None, sim_result=None, sim_error=None,
    sim_status=None, analysis=None, sim_plots=None,
):
    return render_template(
        "index.html",
        form=form,
        mode=mode,
        mode_label=MODE_LABELS[mode],
        mode_fields=MODE_FIELDS[mode],
        result=result,
        error=error,
        unit_label=_unit_label(form.get("unit", "kilo")),
        sim_form=sim_form if sim_form is not None else dict(SIM_DEFAULTS),
        sim_result=sim_result,
        sim_error=sim_error,
        sim_status=sim_status if sim_status is not None else _engine_status(),
        analysis=analysis if analysis in ANALYSES else "dc",
        sim_analysis_labels=SIM_ANALYSIS_LABELS,
        sim_plots=sim_plots if sim_plots is not None else {},
    )


def _collect_form(fallback: bool):
    """Read the form. On a mode switch we keep defaults for untouched fields."""
    source = request.form

    def read(field):
        if field in source:
            return source.get(field, "").strip()
        return DEFAULTS[field] if fallback else ""

    form = {field: read(field) for field in NUMERIC_FIELDS}
    unit = source.get("unit", DEFAULTS["unit"])
    form["unit"] = unit if unit in ("kilo", "ohm") else "kilo"
    return form


@app.get("/")
def index():
    form = dict(DEFAULTS)
    form["mode"] = MODE_DIVIDER
    return _render(form, MODE_DIVIDER)


@app.post("/calculate")
def calculate():
    action = request.form.get("action", "calculate")
    raw_mode = request.form.get("mode", MODE_DIVIDER).strip()
    mode_ok = raw_mode in MODES
    mode = raw_mode if mode_ok else MODE_DIVIDER

    form = _collect_form(fallback=(action == "change_mode"))
    form["mode"] = mode

    if not mode_ok:
        return _render(
            form, mode, error="โหมดไม่ถูกต้อง กรุณาเลือกโหมดวงจรที่กำหนด")

    if action == "change_mode":
        return _render(form, mode)

    required = ("vcc", "beta", "vbe") + MODE_FIELDS[mode]
    if any(not form[field] for field in required):
        return _render(form, mode, error="กรุณากรอกข้อมูลให้ครบทุกช่อง")

    try:
        values = {field: float(form[field]) for field in required}
    except ValueError:
        return _render(form, mode, error="กรุณากรอกเป็นตัวเลข (ห้ามใช้ comma)")

    factor = 1000.0 if form["unit"] == "kilo" else 1.0
    resistors = {
        field: values[field] * factor for field in MODE_FIELDS[mode]
    }

    try:
        if mode == MODE_DIVIDER:
            result = calculate_dc_bias(BiasInputs(
                vcc=values["vcc"],
                r1=resistors["r1"],
                r2=resistors["r2"],
                rc=resistors["rc"],
                re=resistors["re"],
                beta=values["beta"],
                vbe=values["vbe"],
            ))
        elif mode == MODE_FIXED:
            result = calculate_fixed_bias(
                vcc=values["vcc"],
                rb=resistors["rb"],
                rc=resistors["rc"],
                beta=values["beta"],
                vbe=values["vbe"],
            )
        else:
            result = calculate_emitter_bias(
                vcc=values["vcc"],
                rb=resistors["rb"],
                re=resistors["re"],
                rc=resistors["rc"],
                beta=values["beta"],
                vbe=values["vbe"],
            )
    except ValidationError as exc:
        return _render(form, mode, error=str(exc))

    return _render(form, mode, result=result)


def _sim_form():
    """Read the simulation form using namespaced inputs, never raw values."""
    source = request.form
    form = {}
    for field in SIM_PARAM_FIELDS:
        key = f"sim_{field}"
        form[field] = (
            source.get(key, "").strip() if key in source
            else SIM_DEFAULTS[field]
        )
    unit = source.get("sim_unit", SIM_DEFAULTS["sim_unit"]).strip()
    form["sim_unit"] = unit if unit in ("kilo", "ohm") else "kilo"
    analysis = source.get("sim_analysis", SIM_DEFAULTS["analysis"]).strip().lower()
    form["analysis"] = analysis
    return form


def _parse_sim_params(form):
    """Validate text fields and convert to SI values before netlist creation."""
    values = {}
    for field in SIM_PARAM_FIELDS:
        raw = form.get(field, "")
        if not raw:
            raise ValueError("กรุณากรอกข้อมูลให้ครบทุกช่อง")
        try:
            number = float(raw)
        except ValueError as exc:
            raise ValueError("กรุณากรอกเป็นตัวเลข (ห้ามใช้ comma)") from exc
        if not math.isfinite(number):
            raise ValueError("จำนวนต้องเป็นค่าจำกัด (finite)")
        values[field] = number

    if values["vcc"] <= 0:
        raise ValueError("แรงดันแหล่งจ่ายต้องมากกว่า 0")
    if any(values[field] <= 0 for field in SIM_RESISTORS):
        raise ValueError("ค่าความต้านทานต้องมากกว่า 0")
    if values["cin"] <= 0 or values["cout"] <= 0:
        raise ValueError("ค่าความจุต้องมากกว่า 0")
    if values["amplitude"] <= 0:
        raise ValueError("ขนาดสัญญาณอินพุตต้องมากกว่า 0")
    if values["frequency"] <= 0:
        raise ValueError("ความถี่ต้องมากกว่า 0")

    factor = 1000.0 if form["sim_unit"] == "kilo" else 1.0
    return SpiceParams(
        vcc_v=values["vcc"],
        r1_ohm=values["r1"] * factor,
        r2_ohm=values["r2"] * factor,
        rc_ohm=values["rc"] * factor,
        re_ohm=values["re"] * factor,
        rl_ohm=values["rl"] * factor,
        cin_f=values["cin"] * 1e-6,
        cout_f=values["cout"] * 1e-6,
        amplitude_v=values["amplitude"] * 1e-3,
        frequency_hz=values["frequency"] * 1e3,
    )


@app.post("/simulate")
def simulate():
    analysis = request.form.get("sim_analysis", SIM_DEFAULTS["analysis"])
    analysis = analysis.strip().lower()
    form = _sim_form()

    # Keep the Lab 03 form intact on every SPICE response.
    calc_form = _collect_form(fallback=True)
    calc_form["mode"] = MODE_DIVIDER

    if analysis not in ANALYSES:
        return _render(
            calc_form, MODE_DIVIDER,
            sim_form=form,
            sim_error="โหมดการจำลองไม่ถูกต้อง กรุณาเลือก DC / AC / Transient",
            analysis=analysis,
        )

    try:
        params = _parse_sim_params(form)
    except ValueError as exc:
        return _render(
            calc_form, MODE_DIVIDER,
            sim_form=form, sim_error=str(exc), analysis=analysis,
        )

    try:
        result = run_simulation(params, analysis)
    except SpiceError as exc:
        return _render(
            calc_form, MODE_DIVIDER,
            sim_form=form,
            sim_error=f"การจำลอง SPICE ล้มเหลว: {exc}",
            sim_status=_engine_status("failed"),
            analysis=analysis,
        )

    plots = {}
    if analysis == "ac" and result.ac:
        plots["bode"] = bode_svg(result.ac, params.amplitude_v)
    elif analysis == "transient" and result.tran:
        plots["transient"] = transient_svg(result.tran)

    return _render(
        calc_form, MODE_DIVIDER,
        sim_form=form,
        sim_result=result,
        sim_status=_engine_status("success"),
        analysis=analysis,
        sim_plots=plots,
    )


if __name__ == "__main__":
    app.run(debug=True)
