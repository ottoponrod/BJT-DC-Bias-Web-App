# Lab 04 CE Amplifier Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real ngspice DC/AC/Transient simulation for one reference CE amplifier to the existing Lab 03 Flask app without regressing any analytical bias mode.

**Architecture:** Keep `/calculate` and `dc_bias.py` untouched. Add `spice_engine.py` that generates one netlist per analysis, runs ngspice 47 in a temp cwd via a safe `subprocess.run` list call, parses the ASCII tables in the `-o` log, and returns typed results or raises `SpiceError`. Add a separate `/simulate` form and server-rendered SVG plots in the existing template.

**Tech Stack:** Python 3.13, Flask 3.1, external ngspice 47, `unittest`, vanilla JS, server-side SVG.

**Spec:** `docs/superpowers/specs/2026-11-24-ce-amplifier-simulator-design.md` and the Lab 04 handout HTML.

## Global Constraints

- Keep all three Lab 03 analytical bias modes and all 50 existing tests passing.
- No new required Python dependencies; plots are SVG generated from parsed data.
- `subprocess.run` with a list of arguments, `shell=False`, explicit `timeout`,
  unique `tempfile.TemporaryDirectory()` per run.
- Reject invalid input before creating a netlist; never interpolate raw form
  strings into a netlist.
- Missing engine, nonzero exit, empty log, timeout, or parse failure must be
  surfaced as an error with **no** result table and **no** success status.
- Use `.model QNPN NPN(BF=100 IS=1e-14 VAF=100)` and name it in UI + validation
  as a self-defined reference, not an instructor model.
- `vp()` values from `.print ac` are radians: convert to degrees.
- No hard-coded plot data; every plotted point comes from a parsed ngspice log.

## Review Focus

- Form text such as `0`, `-5`, `abc`, `1e309`, comma-separated numbers →
  explicit Thai error, no netlist, no success.
- ngspice missing or returning nonzero → error status, no stale result.
- Empty/partial log or timeout → error, not an empty "Success" graph.
- Changing RE or source amplitude/frequency → numbers and plots change on the
  next run (B3/B6).
- `vp()` radians vs degrees → phase labelled in degrees and near −180° at
  midband for the inverting CE stage.

---

### Task 1: SPICE engine — netlist, runner, parsers

**Files:**
- Create: `spice_engine.py`
- Create: `tests/test_spice_engine.py`

**Interfaces:**
- Produces: `SpiceParams`, `SimulationResult`, `SpiceError`, `ANALYSES`,
  `find_ngspice()`, `build_netlist(params, analysis) -> str`,
  `parse_op_log(text) -> dict[str, float]`,
  `parse_ac_log(text) -> list[dict[str, float]]`,
  `parse_tran_log(text) -> list[dict[str, float]]`,
  `run_simulation(params, analysis, *, executable=None, timeout=30) -> SimulationResult`
- `SimulationResult` fields: `analysis`, `model`, `netlist`, `log_excerpt`,
  `op: dict | None`, `ac: list | None`, `tran: list | None`,
  `summary: dict[str, float]`.

- [ ] **Step 1: Write failing parser tests** using small literal log fragments
  from the real ngspice format: op node table (`nb`, `ne`, `nc`, `nvcc`),
  AC table (`Index frequency vdb(nout) vp(nout)`), TRAN table
  (`Index time v(nin) v(nout)`). Assert parsed values, units, and rad→deg.

- [ ] **Step 2: Run them and confirm FAIL** (`function not defined`).

- [ ] **Step 3: Implement dataclasses, constants, `find_ngspice`, netlist
  builder and the three pure parsers.** Netlist must start with a `* CE
  amplifier` title comment, then VCC/VIN/R1/R2/RC/RE/Q1/CIN/COUT/RL,
  `.model QNPN NPN(BF=100 IS=1e-14 VAF=100)`, then exactly one analysis plus a
  `.print` line and `.end`. AC sweep `dec 40 10 10Meg`; TRAN `0.01m 5m`.

- [ ] **Step 4: Implement `run_simulation`** with `tempfile.TemporaryDirectory`,
  `subprocess.run([exe, "-b", "-o", log, netlist], cwd=tmp, timeout=timeout,
  capture_output=True, text=True)`. Raise `SpiceError` on missing engine,
  nonzero return code, empty log, or parser returning no rows. Compute `IC`
  from `(VCC - VC)/RC` and midband gain / −3 dB point for AC.

- [ ] **Step 5: Add one real-ngspice smoke test** per analysis (skip if engine
  absent) asserting non-empty op/ac/tran and finite values. Run all tests.

- [ ] **Step 6: Commit** `spice_engine.py` and `tests/test_spice_engine.py`.

### Task 2: Flask `/simulate` route and validation

**Files:**
- Modify: `app.py`
- Create: `tests/test_simulate_web.py`

**Interfaces:**
- Consumes: Task 1 API.
- Produces: `SIM_DEFAULTS`, `SIM_PARAM_FIELDS`, `render` context keys
  `sim_form`, `sim_result`, `sim_error`, `sim_status`, `analysis`.

- [ ] **Step 1: Write failing Flask tests** for: GET `/` shows simulation form;
  POST `/simulate` DC gives VB/VE/VC/VCE/IC and engine status; `RE=0` gives
  error without result; non-numeric amplitude gives error; unknown analysis
  rejected; monkeypatched `run_simulation` raising `SpiceError` still returns
  HTTP 200 with error and **no** success text.

- [ ] **Step 2: Confirm FAIL, then implement** validation (all numeric finite,
  positive resistors/source/frequency, amplitude > 0) and dispatch. Convert
  kΩ/Ω inputs to ohms. Never pass raw strings into `SpiceParams`.

- [ ] **Step 3: Run full suite** (existing 50 + new) and confirm all pass.

- [ ] **Step 4: Commit.**

### Task 3: Results UI — provenance, tables, real-data plots

**Files:**
- Modify: `templates/index.html`, `static/style.css`

**Interfaces:**
- Consumes: Task 2 context.

- [ ] **Step 1: Add simulation form** below the existing bias form: analysis
  select (dc/ac/transient), VCC/R1/R2/RC/RE/RL/CIN/COUT/AMPLITUDE/FREQUENCY
  fields with units, Run Simulation button, and a status badge showing engine,
  model and run status. Keep the existing bias form's IDs and names unchanged.

- [ ] **Step 2: Add result sections** that only render when `sim_result` is
  present: DC table (VB, VE, VC, VCE, IC with units and "ngspice .op" label);
  AC SVG with frequency (Hz, log axis), gain (dB) and phase (deg) panels;
  TRAN SVG with time (ms) and Vin/Vout (V) legend. Show error panel otherwise.

- [ ] **Step 3: Add a provenance note** separating "Analytical (Lab 03)" from
  "SPICE (ngspice 47, model QNPN ...)" and print `−3 dB` result or
  "not determined in sweep range".

- [ ] **Step 4: Verify with Flask test client** that result markup contains
  axis units, model label, and no plot data when an error is set. Commit.

### Task 4: Impeccable UI review and polish

**Files:**
- Modify only `static/style.css`, `templates/index.html`, `static/app.js`
- Add: `docs/captures/ui-before.png`, `docs/captures/ui-after.png`

**Interfaces:** Consumes Tasks 2–3.

- [ ] **Step 1: Load the installed Impeccable skill** from
  `.opencode/skills/impeccable/SKILL.md` (or via a new OpenCode session) and
  critique the running page at `http://127.0.0.1:5000/`.

- [ ] **Step 2: Capture before screenshots** at desktop ~1280 px and mobile
  ~390 px with the in-app browser.

- [ ] **Step 3: Apply only UI-only improvements**: input grouping, readable
  legends/units, error state, responsive layout, visible engine status. Do not
  touch formulas, netlist, parser or data path.

- [ ] **Step 4: Re-run all tests and B1-style regression**; capture after
  screenshots; commit with before/after note in `docs/validation.md`.

### Task 5: Browser acceptance B1–B8, docs, commit/push

**Files:**
- Create/modify: `docs/validation.md`, `README.md`, `docs/captures/*.png`

**Interfaces:** Consumes all earlier tasks.

- [ ] **Step 1: Restart Flask** so it loads the new code; confirm HTTP 200.

- [ ] **Step 2: Run B1–B8 in the real browser** with Navigate → Snapshot →
  Fill → Click → Snapshot → Read → Compare → Screenshot. For B4/B5/B6 compare
  plotted values with the ngspice log/result object, not the screenshot alone.

- [ ] **Step 3: Record a PASS/FAIL/NOT RUN table** in `docs/validation.md`
  with case, method, input, expected, observed, units, evidence, status;
  include ngspice version, the QNPN model declaration and limitations.

- [ ] **Step 4: Update README** with ngspice install/PATH steps, `pip install -r
  requirements.txt`, run command, browser URL and how to reproduce a run.

- [ ] **Step 5: Run full test suite one final time**, then commit and push
  (CLI push may need GitHub Desktop). Report commit SHA honestly.
