"""Flask application for the BJT DC bias calculator (Lab 02)."""

from flask import Flask, render_template, request

from dc_bias import BiasInputs, ValidationError, calculate_dc_bias

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
    "unit": "kilo",
}

NUMERIC_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
RESISTOR_FIELDS = ("r1", "r2", "rc", "re")


def _unit_label(unit: str) -> str:
    return "kΩ" if unit == "kilo" else "Ω"


def _render(form, result=None, error=None):
    return render_template(
        "index.html",
        form=form,
        result=result,
        error=error,
        unit_label=_unit_label(form.get("unit", "kilo")),
    )


@app.get("/")
def index():
    return _render(DEFAULTS)


@app.post("/calculate")
def calculate():
    form = {field: request.form.get(field, "").strip() for field in NUMERIC_FIELDS}
    unit = request.form.get("unit", "kilo")
    form["unit"] = unit if unit in ("kilo", "ohm") else "kilo"

    if any(not form[field] for field in NUMERIC_FIELDS):
        return _render(form, error="กรุณากรอกข้อมูลให้ครบทุกช่อง")

    try:
        values = {field: float(form[field]) for field in NUMERIC_FIELDS}
    except ValueError:
        return _render(form, error="กรุณากรอกเป็นตัวเลข (ห้ามใช้ comma)")

    factor = 1000.0 if form["unit"] == "kilo" else 1.0
    inputs = BiasInputs(
        vcc=values["vcc"],
        r1=values["r1"] * factor,
        r2=values["r2"] * factor,
        rc=values["rc"] * factor,
        re=values["re"] * factor,
        beta=values["beta"],
        vbe=values["vbe"],
    )

    try:
        result = calculate_dc_bias(inputs)
    except ValidationError as exc:
        return _render(form, error=str(exc))

    return _render(form, result=result)


if __name__ == "__main__":
    app.run(debug=True)
