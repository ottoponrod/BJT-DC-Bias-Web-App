"""Server-rendered SVG plots built only from parsed ngspice arrays.

No values are sampled, smoothed or invented here: every plotted point comes
from a row parsed out of an actual ngspice ``-o`` log by ``spice_engine``.
"""

from __future__ import annotations

import math

_PLOT_WIDTH = 860
_X0, _X1 = 72, 834


def _fmt(value: float) -> str:
    return f"{value:.5g}"


def _points(pairs) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pairs)


def _x_log(frequency: float, low: float, high: float) -> float:
    return _X0 + (math.log10(frequency) - low) / (high - low) * (_X1 - _X0)


def _panel(values, top: float, bottom: float, colour: str, label: str) -> str:
    finite = [v for v in values if math.isfinite(v)]
    low, high = min(finite), max(finite)
    if low == high:
        low, high = low - 1.0, high + 1.0
    padding = 0.06 * (high - low)
    low, high = low - padding, high + padding

    def y(value: float) -> float:
        return bottom - (value - low) / (high - low) * (bottom - top)

    grid = []
    for fraction in (0.0, 0.5, 1.0):
        level = low + fraction * (high - low)
        gy = y(level)
        grid.append(
            f'<line x1="{_X0}" y1="{gy:.2f}" x2="{_X1}" y2="{gy:.2f}" '
            f'class="grid"/>'
            f'<text x="{_X0 - 8}" y="{gy + 4:.2f}" class="tick" '
            f'text-anchor="end">{_fmt(level)}</text>'
        )
    grid.append(
        f'<text x="{_X0}" y="{top - 10}" class="axis-label" '
        f'fill="{colour}">{label}</text>'
    )
    return "\n".join(grid), y


def _log_ticks(low: float, high: float) -> str:
    ticks = []
    for exponent in range(math.floor(low), math.ceil(high) + 1):
        if not low <= exponent <= high:
            continue
        x = _X0 + (exponent - low) / (high - low) * (_X1 - _X0)
        ticks.append(
            f'<line x1="{x:.2f}" y1="36" x2="{x:.2f}" y2="392" class="grid"/>'
            f'<text x="{x:.2f}" y="408" class="tick" '
            f'text-anchor="middle">1e{exponent}</text>'
        )
    return "\n".join(ticks)


def bode_svg(rows, amplitude_v: float) -> str:
    """Return a two-panel Bode plot: relative gain (dB) and phase (deg)."""
    data = []
    for row in rows:
        frequency = row["frequency_hz"]
        gain = row["gain_dbv"] - 20.0 * math.log10(amplitude_v)
        phase = row["phase_deg"]
        if all(math.isfinite(v) for v in (frequency, gain, phase)) and frequency > 0:
            data.append((frequency, gain, phase))
    if not data:
        return '<svg class="plot" viewBox="0 0 860 430"><text>No SPICE data</text></svg>'

    log_low = math.log10(min(row[0] for row in data))
    log_high = math.log10(max(row[0] for row in data))
    if log_low == log_high:
        log_low, log_high = log_low - 0.5, log_high + 0.5

    gains = [row[1] for row in data]
    phases = [row[2] for row in data]
    gain_grid, gain_y = _panel(gains, 44, 186, "#1d638b", "gain (dB)")
    phase_grid, phase_y = _panel(phases, 246, 388, "#b85c2c", "phase (deg)")
    gain_line = _points(
        [(_x_log(row[0], log_low, log_high), gain_y(row[1])) for row in data]
    )
    phase_line = _points(
        [(_x_log(row[0], log_low, log_high), phase_y(row[2])) for row in data]
    )

    return f"""<svg class="plot" viewBox="0 0 860 430" role="img"
     aria-label="Bode plot from parsed ngspice AC sweep">
  <rect x="0" y="0" width="860" height="430" class="plot-bg"/>
  {gain_grid}
  {phase_grid}
  {_log_ticks(log_low, log_high)}
  <polyline points="{gain_line}" class="line-gain"/>
  <polyline points="{phase_line}" class="line-phase"/>
  <text x="453" y="428" class="axis-label" text-anchor="middle">frequency (Hz)</text>
</svg>"""


def transient_svg(rows) -> str:
    """Return a time-domain plot of parsed Vin and Vout, with time in ms."""
    data = []
    for row in rows:
        time_ms = row["time_s"] * 1000.0
        vin, vout = row["vin_v"], row["vout_v"]
        if all(math.isfinite(v) for v in (time_ms, vin, vout)):
            data.append((time_ms, vin, vout))
    if not data:
        return '<svg class="plot" viewBox="0 0 860 330"><text>No SPICE data</text></svg>'

    tmax = max(row[0] for row in data)
    if tmax <= 0:
        tmax = 1.0
    voltages = [value for row in data for value in (row[1], row[2])]
    low, high = min(voltages), max(voltages)
    if low == high:
        low, high = low - 1.0, high + 1.0
    padding = 0.08 * (high - low)
    low, high = low - padding, high + padding

    def x(time_ms: float) -> float:
        return _X0 + time_ms / tmax * (_X1 - _X0)

    def y(value: float) -> float:
        return 286 - (value - low) / (high - low) * (286 - 36)

    grid = []
    for fraction in (0.0, 0.5, 1.0):
        level = low + fraction * (high - low)
        gy = y(level)
        grid.append(
            f'<line x1="{_X0}" y1="{gy:.2f}" x2="{_X1}" y2="{gy:.2f}" '
            f'class="grid"/>'
            f'<text x="{_X0 - 8}" y="{gy + 4:.2f}" class="tick" '
            f'text-anchor="end">{_fmt(level)}</text>'
        )
    for fraction in (0.0, 0.5, 1.0):
        tx = _X0 + fraction * (_X1 - _X0)
        grid.append(
            f'<text x="{tx:.2f}" y="306" class="tick" text-anchor="middle">'
            f'{_fmt(fraction * tmax)}</text>'
        )

    vin_line = _points([(x(row[0]), y(row[1])) for row in data])
    vout_line = _points([(x(row[0]), y(row[2])) for row in data])

    return f"""<svg class="plot" viewBox="0 0 860 330" role="img"
     aria-label="Transient plot from parsed ngspice time domain data">
  <rect x="0" y="0" width="860" height="330" class="plot-bg"/>
  {''.join(grid)}
  <polyline points="{vin_line}" class="line-vin"/>
  <polyline points="{vout_line}" class="line-vout"/>
  <text x="453" y="326" class="axis-label" text-anchor="middle">time (ms)</text>
  <g class="legend">
    <line x1="640" y1="22" x2="670" y2="22" class="line-vin"/>
    <text x="676" y="26" class="axis-label">Vin [V]</text>
    <line x1="640" y1="40" x2="670" y2="40" class="line-vout"/>
    <text x="676" y="44" class="axis-label">Vout [V]</text>
  </g>
</svg>"""
