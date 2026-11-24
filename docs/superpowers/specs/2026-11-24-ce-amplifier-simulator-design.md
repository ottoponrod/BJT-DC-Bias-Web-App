# Lab 04 — BJT CE Amplifier Simulator v1 Design

**Date:** 2026-11-24
**Source spec:** `C:\Users\B6809737\Downloads\Lab04_BJT_Amplifier_Simulator_2-2569.html`

## Intent

Extend the existing Flask Lab 03 DC-bias app into a working Common-Emitter
amplifier simulator: keep the three analytical bias modes and their tests
untouched, and add **real** ngspice DC / AC / Transient results for one
reference voltage-divider CE circuit. Students must be able to see where every
number came from and reproduce the run.

## Goals

- Preserve `dc_bias.py`, `app.py`'s `/calculate` route, templates, CSS, JS and
  all 50 existing tests verbatim in behaviour.
- Add `spice_engine.py`: build a netlist, run external ngspice via
  `subprocess.run` (argument list, no `shell=True`, timeout, per-run temp cwd),
  parse log text, expose typed results, raise on every failure path.
- Add a separate `/simulate` form on the same page: analysis mode (DC/AC/Tran),
  source amplitude and frequency, plus circuit parameters. Validate before
  netlist generation.
- Display DC operating point, Bode magnitude/phase and transient Vin/Vout from
  actual ngspice output, with axes, units, engine status, model name and a
  clear SPICE-vs-analytical provenance label.
- Verify B1–B8 in a real browser and record evidence in `docs/validation.md`.

## Non-goals / anti-goals

- No drag-and-drop editor, no arbitrary topology, no AC for Fixed/Emitter, no
  FET, no custom SPICE solver, no animated circuit overlay, no deployment.
- No emitter-bypass capacitor in the baseline (optional extension only).
- **Never** fabricate traces, hard-code plotted values, or show a stale success
  result when ngspice failed / timed out / returned empty output.
- Never invent a cutoff frequency: if no −3 dB crossing exists in the sweep,
  report "not determined in sweep range".

## Constraints and decisions

- Python 3.13, Flask `>=3.0,<4.0`, `unittest` only. No new required Python
  package: plots are server-rendered SVG from parsed arrays.
- ngspice 47 installed at
  `C:\Users\B6809737\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice.exe`
  and on the User PATH. Discovered with `shutil.which("ngspice")` plus this
  explicit Windows fallback.
- **No instructor Starter Kit was present.** Therefore this app uses an
  explicit, documented reference model:
  `.model QNPN NPN(BF=100 IS=1e-14 VAF=100)`.
  This is our own reference model, not an instructor-verified part. It must be
  named in the UI and in `docs/validation.md` as a stated limitation.
- One ngspice process **per analysis** (separate `.op`, `.ac`, `.tran` netlists
  in separate temp directories). Multi-analysis netlists were probed and
  ngspice 47 batch mode aborts the transient run in that combination.
- Node names avoid SPICE reserved words: `NVCC NIN NB NE NC NOUT`.
- Reference fixture: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ,
  RL 10 kΩ, CIN = COUT = 10 µF, source 10 mV peak, 1 kHz.
- Parsed `.op` node voltages: `nb`, `ne`, `nc`, `nvcc`; IC = (VCC − VC)/RC.
- Parsed `.ac` table columns from `.print ac vdb(nout) vp(nout)`: index,
  frequency (Hz), gain (dBV), phase (**radians** → convert to degrees). Gain
  relative to the ideal source: `gain_db = vdb(nout) − 20·log10(amplitude)`.
- Parsed `.tran` table: index, time (s), `v(nin)`, `v(nout)` (V).
- Cutoff search uses the midband maximum gain as the −3 dB reference.

## Approaches considered

1. **Separate `/simulate` panel (chosen).** Zero risk to Lab 03 regression;
   clean separation of analytical and SPICE results; one extra route.
2. Extend `/calculate` with an analysis selector. Fewer routes but entangles
   the validated Lab 03 path with new failure modes and would risk B1.
3. Replace the app with a new simulator. Rejected: handout forbids rebuilding.

## Files

- Create: `spice_engine.py`, `tests/test_spice_engine.py`,
  `docs/validation.md`, `docs/captures/` (screenshots)
- Modify: `app.py` (add `/simulate` + validation + render context),
  `templates/index.html` (simulation panel + plots + provenance),
  `static/style.css`, `static/app.js` (label updates only), `README.md`
- Untouched: `dc_bias.py`, `tests/test_dc_bias.py`, `tests/test_web.py`
