"""Real ngspice engine for the reference common-emitter amplifier (Lab 04).

Every value returned by this module comes from an external ngspice run.  The
engine builds one netlist per analysis, runs ngspice in a private temporary
directory and parses the ASCII tables written to the ``-o`` log.  Failures
raise :class:`SpiceError`; no result is ever invented or reused.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

MODEL_NAME = "QNPN"
MODEL_DECLARATION = ".model QNPN NPN(BF=100 IS=1e-14 VAF=100)"
ANALYSES = ("dc", "ac", "transient")

# The Windows ngspice install is not always visible to a GUI-launched Flask
# process, so keep the explicit install path as a fallback after PATH lookup.
_NGSPICE_FALLBACK = (
    r"C:\Users\B6809737\AppData\Local\Programs\ngspice-47"
    r"\Spice64\bin\ngspice.exe"
)

_NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


class SpiceError(RuntimeError):
    """Raised when a simulation cannot be run or its output cannot be trusted."""


@dataclass(frozen=True)
class SpiceParams:
    """Validated circuit values in base SI units (V, ohm, F, Hz)."""

    vcc_v: float
    r1_ohm: float
    r2_ohm: float
    rc_ohm: float
    re_ohm: float
    rl_ohm: float
    cin_f: float
    cout_f: float
    amplitude_v: float
    frequency_hz: float


@dataclass
class SimulationResult:
    """One real ngspice run, its source netlist and the derived summary."""

    analysis: str
    model: str
    netlist: str
    log_excerpt: str
    op: dict[str, float] | None = None
    ac: list[dict[str, float]] | None = None
    tran: list[dict[str, float]] | None = None
    summary: dict[str, float] = field(default_factory=dict)


def find_ngspice() -> str | None:
    """Return an ngspice executable path from PATH or the known install."""
    found = shutil.which("ngspice")
    if found:
        return found
    if os.name == "nt" and Path(_NGSPICE_FALLBACK).is_file():
        return _NGSPICE_FALLBACK
    return None


def build_netlist(params: SpiceParams, analysis: str) -> str:
    """Build a netlist for exactly one SPICE analysis."""
    if analysis not in ANALYSES:
        raise SpiceError(f"Unsupported analysis: {analysis!r}")

    def value(number: float) -> str:
        return f"{number:.6g}"

    lines = [
        "* CE amplifier",
        f"VCC NVCC 0 DC {value(params.vcc_v)}",
        "VIN NIN 0 DC 0 "
        f"AC {value(params.amplitude_v)} "
        f"SIN(0 {value(params.amplitude_v)} {value(params.frequency_hz)})",
        f"R1 NVCC NB {value(params.r1_ohm)}",
        f"R2 NB 0 {value(params.r2_ohm)}",
        f"RC NVCC NC {value(params.rc_ohm)}",
        f"RE NE 0 {value(params.re_ohm)}",
        "Q1 NC NB NE 0 QNPN",
        f"CIN NIN NB {value(params.cin_f)}",
        f"COUT NC NOUT {value(params.cout_f)}",
        f"RL NOUT 0 {value(params.rl_ohm)}",
        MODEL_DECLARATION,
    ]

    if analysis == "dc":
        lines += [".op", ".print op v(nvcc)", ".end"]
    elif analysis == "ac":
        lines += [".ac dec 40 10 10Meg", ".print ac vdb(nout) vp(nout)", ".end"]
    else:
        lines += [".tran 0.01m 5m", ".print tran v(nin) v(nout)", ".end"]
    return "\n".join(lines) + "\n"


def parse_op_log(text: str) -> dict[str, float]:
    """Parse the four reference node voltages from an ``.op`` log table.

    Only the ``Node ... Voltage`` section is considered.  The later BJT model
    dump uses the same identifiers (``ne``/``nc``) for model parameters, and
    reading those would silently replace real node voltages.
    """
    row = re.compile(
        rf"^\s*(nvcc|nb|ne|nc)\s+({_NUMBER})\s*$", re.IGNORECASE
    )
    header = re.compile(r"^\s*Node\s+Voltage\s*$", re.IGNORECASE)
    section_end = re.compile(
        r"^\s*(?:Source|BJT models|Small signal)", re.IGNORECASE
    )
    nodes: dict[str, float] = {}
    in_node_table = False
    for line in text.splitlines():
        if header.match(line):
            in_node_table = True
            continue
        if not in_node_table:
            continue
        if section_end.match(line):
            break
        match = row.match(line)
        if match:
            nodes[match.group(1).lower()] = float(match.group(2))
    return nodes


def parse_ac_log(text: str) -> list[dict[str, float]]:
    """Parse ``.print ac vdb(nout) vp(nout)`` rows; vp is radians in SPICE."""
    row = re.compile(
        rf"^\s*(\d+)\s+({_NUMBER})\s+({_NUMBER})\s+({_NUMBER})\s*$"
    )
    parsed: list[dict[str, float]] = []
    for line in text.splitlines():
        match = row.match(line)
        if match:
            phase_rad = float(match.group(4))
            parsed.append(
                {
                    "index": float(match.group(1)),
                    "frequency_hz": float(match.group(2)),
                    "gain_dbv": float(match.group(3)),
                    "phase_rad": phase_rad,
                    "phase_deg": math.degrees(phase_rad),
                }
            )
    return parsed


def parse_tran_log(text: str) -> list[dict[str, float]]:
    """Parse ``.print tran v(nin) v(nout)`` rows into SI values."""
    row = re.compile(
        rf"^\s*(\d+)\s+({_NUMBER})\s+({_NUMBER})\s+({_NUMBER})\s*$"
    )
    parsed: list[dict[str, float]] = []
    for line in text.splitlines():
        match = row.match(line)
        if match:
            parsed.append(
                {
                    "index": float(match.group(1)),
                    "time_s": float(match.group(2)),
                    "vin_v": float(match.group(3)),
                    "vout_v": float(match.group(4)),
                }
            )
    return parsed


def _dc_summary(op: dict[str, float], params: SpiceParams) -> dict[str, float]:
    return {
        "vcc": op["nvcc"],
        "vb": op["nb"],
        "ve": op["ne"],
        "vc": op["nc"],
        "vce": op["nc"] - op["ne"],
        "ic_ma": (op["nvcc"] - op["nc"]) / params.rc_ohm * 1000.0,
    }


def _ac_summary(
    rows: list[dict[str, float]], params: SpiceParams
) -> dict[str, float]:
    midband = max(rows, key=lambda row: row["gain_dbv"])
    gain_db = midband["gain_dbv"] - 20.0 * math.log10(params.amplitude_v)
    target_db = midband["gain_dbv"] - 3.0
    f3db = None
    for low, high in zip(rows, rows[1:]):
        if low["gain_dbv"] >= target_db >= high["gain_dbv"]:
            span = high["gain_dbv"] - low["gain_dbv"]
            if span == 0:
                f3db = low["frequency_hz"]
            else:
                fraction = (target_db - low["gain_dbv"]) / span
                f3db = low["frequency_hz"] * (
                    high["frequency_hz"] / low["frequency_hz"]
                ) ** fraction
            break

    at_source = min(
        rows, key=lambda row: abs(row["frequency_hz"] - params.frequency_hz)
    )
    return {
        "midband_gain_db": gain_db,
        "f3db_hz": f3db,
        "phase_deg": at_source["phase_deg"],
        "source_amplitude_v": params.amplitude_v,
    }


def _tran_summary(rows: list[dict[str, float]]) -> dict[str, float]:
    return {
        "peak_vin_v": max(abs(row["vin_v"]) for row in rows),
        "peak_vout_v": max(abs(row["vout_v"]) for row in rows),
    }


def run_simulation(
    params: SpiceParams,
    analysis: str,
    *,
    executable: str | None = None,
    timeout: float = 30,
) -> SimulationResult:
    """Run one real ngspice analysis and return parsed, provenance-tagged data."""
    if analysis not in ANALYSES:
        raise SpiceError(f"Unsupported analysis: {analysis!r}")
    exe = executable or find_ngspice()
    if not exe:
        raise SpiceError(
            "ngspice executable not found. Install ngspice 47 and add it to PATH."
        )

    netlist = build_netlist(params, analysis)
    with tempfile.TemporaryDirectory(prefix="ce_spice_") as tmp:
        netlist_path = Path(tmp) / "circuit.cir"
        log_path = Path(tmp) / "result.log"
        netlist_path.write_text(netlist, encoding="ascii")

        try:
            completed = subprocess.run(
                [exe, "-b", "-o", str(log_path), str(netlist_path)],
                cwd=tmp,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise SpiceError(
                f"ngspice timed out after {timeout} seconds; no results returned."
            ) from exc
        except OSError as exc:
            raise SpiceError(f"Could not start ngspice: {exc}") from exc

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise SpiceError(
                f"ngspice exited with status {completed.returncode}: {detail[:200]}"
            )
        if not log_path.exists():
            raise SpiceError("ngspice produced no output log; no results available.")
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        if not log_text.strip():
            raise SpiceError("ngspice produced an empty log; no results available.")
        if any(line.startswith("Error:") for line in log_text.splitlines()):
            raise SpiceError("ngspice reported an error in its output log.")
        log_excerpt = "\n".join(log_text.splitlines()[:40])

    op = ac = tran = None
    if analysis == "dc":
        op = parse_op_log(log_text)
        if not {"nvcc", "nb", "ne", "nc"}.issubset(op):
            raise SpiceError("Could not parse the ngspice operating point table.")
        summary = _dc_summary(op, params)
    elif analysis == "ac":
        ac = parse_ac_log(log_text)
        if not ac:
            raise SpiceError("Could not parse the ngspice AC sweep table.")
        summary = _ac_summary(ac, params)
    else:
        tran = parse_tran_log(log_text)
        if not tran:
            raise SpiceError("Could not parse the ngspice transient table.")
        summary = _tran_summary(tran)

    return SimulationResult(
        analysis=analysis,
        model=f"{MODEL_NAME} NPN(BF=100 IS=1e-14 VAF=100)",
        netlist=netlist,
        log_excerpt=log_excerpt,
        op=op,
        ac=ac,
        tran=tran,
        summary=summary,
    )
