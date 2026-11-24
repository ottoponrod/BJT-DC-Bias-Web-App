"""Tests for the real-ngspice SPICE engine (Task 1)."""

import math
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from spice_engine import (
    MODEL_DECLARATION,
    SpiceError,
    _ac_summary,
    SpiceParams,
    ANALYSES,
    build_netlist,
    find_ngspice,
    parse_ac_log,
    parse_op_log,
    parse_tran_log,
    run_simulation,
)


REFERENCE_PARAMS = SpiceParams(
    vcc_v=12.0,
    r1_ohm=100_000.0,
    r2_ohm=22_000.0,
    rc_ohm=2_200.0,
    re_ohm=1_000.0,
    rl_ohm=10_000.0,
    cin_f=10e-6,
    cout_f=10e-6,
    amplitude_v=0.01,
    frequency_hz=1000.0,
)


class FakeNgspice:
    """Stand-in for the external process: writes the log ngspice would write."""

    def __init__(self, log_text: str, returncode: int = 0, exception=None):
        self.log_text = log_text
        self.returncode = returncode
        self.exception = exception
        self.args = None
        self.kwargs = None

    def __call__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        if self.exception is not None:
            raise self.exception
        Path(args[3]).write_text(self.log_text, encoding="utf-8")
        return subprocess.CompletedProcess(args, self.returncode, "", "")


OP_LOG = """\tNode                                  Voltage
\t----                                  -------
\tnout                             0.000000e+00
\tne                               1.289454e+00
\tnc                               9.189410e+00
\tnb                               1.949112e+00
\tnin                              0.000000e+00
\tnvcc                             1.200000e+01

\tSource\tCurrent
\t------\t-------
\tvcc#branch                       -1.37805e-03
"""

AC_LOG = """--------------------------------------------------------------------------------
Index   frequency       vdb(nout)       vp(nout)
--------------------------------------------------------------------------------
0\t1.000000e+01\t-6.10349e+01\t1.004770e-01
40\t1.000000e+03\t-6.09999e+01\t1.007130e-03
80\t1.000000e+04\t-6.200000e+01\t-1.570796e+00
"""

TRAN_LOG = """--------------------------------------------------------------------------------
Index   time            v(nin)          v(nout)
--------------------------------------------------------------------------------
0\t0.000000e+00\t0.000000e+00\t0.000000e+00
1\t1.000000e-07\t6.283185e-06\t-3.40928e-05
2\t1.000000e-03\t1.000000e-02\t-4.860000e-02
"""

# Summary tests use complete-looking sweeps: the fixed netlist sweeps 10 Hz to
# 10 MHz (AC) and 0 to 5 ms (transient).  The shorter AC_LOG / TRAN_LOG above
# stay as parser fixtures and double as truncated-log regression inputs.
AC_LOG_COMPLETE = AC_LOG + "120\t1.000000e+07\t-6.200000e+01\t-1.570796e+00\n"
TRAN_LOG_COMPLETE = TRAN_LOG + "3\t5.000000e-03\t0.000000e+00\t0.000000e+00\n"


class TestParseOpLog(unittest.TestCase):
    def test_reads_only_reference_nodes_from_operating_point_table(self):
        parsed = parse_op_log(OP_LOG)

        self.assertAlmostEqual(parsed["nvcc"], 12.0)
        self.assertAlmostEqual(parsed["nb"], 1.949112)
        self.assertAlmostEqual(parsed["ne"], 1.289454)
        self.assertAlmostEqual(parsed["nc"], 9.189410)
        self.assertEqual(set(parsed), {"nvcc", "nb", "ne", "nc"})

    def test_ignores_bjt_model_parameters_that_share_node_names(self):
        contaminated = OP_LOG + """\n BJT models (Bipolar Junction Transistor)
      model                  qnpn
       type                   npn
         is                 1e-14
         ne                   1.5
         nc                   2.0
"""
        parsed = parse_op_log(contaminated)

        self.assertAlmostEqual(parsed["ne"], 1.289454)
        self.assertAlmostEqual(parsed["nc"], 9.189410)

    def test_returns_empty_dict_when_no_node_table_present(self):
        self.assertEqual(parse_op_log("no simulation here"), {})


class TestParseAcLog(unittest.TestCase):
    def test_reads_frequency_gain_and_converts_phase_to_degrees(self):
        rows = parse_ac_log(AC_LOG)

        self.assertEqual(len(rows), 3)
        self.assertAlmostEqual(rows[0]["frequency_hz"], 10.0)
        self.assertAlmostEqual(rows[0]["gain_dbv"], -61.0349)
        self.assertAlmostEqual(rows[1]["frequency_hz"], 1000.0)
        self.assertAlmostEqual(rows[1]["gain_dbv"], -60.9999)
        self.assertAlmostEqual(rows[1]["phase_deg"], 0.0577, delta=0.001)
        self.assertAlmostEqual(rows[2]["phase_deg"], -90.0, delta=0.01)

    def test_keeps_raw_phase_radians_alongside_degrees(self):
        row = parse_ac_log(AC_LOG)[2]

        self.assertAlmostEqual(row["phase_rad"], -1.570796)

    def test_returns_empty_list_when_no_ac_table_present(self):
        self.assertEqual(parse_ac_log("Index   frequency   vdb(nout)"), [])


class TestParseTranLog(unittest.TestCase):
    def test_reads_time_vin_and_vout_from_transient_table(self):
        rows = parse_tran_log(TRAN_LOG)

        self.assertEqual(len(rows), 3)
        self.assertAlmostEqual(rows[1]["time_s"], 1e-7)
        self.assertAlmostEqual(rows[1]["vin_v"], 6.283185e-6)
        self.assertAlmostEqual(rows[1]["vout_v"], -3.40928e-5)
        self.assertAlmostEqual(rows[2]["time_s"], 1e-3)

    def test_returns_empty_list_when_no_transient_table_present(self):
        self.assertEqual(parse_tran_log("Index   time   v(nin)"), [])


class TestBuildNetlist(unittest.TestCase):
    def test_netlist_contains_reference_circuit_and_exactly_one_dc_analysis(self):
        netlist = build_netlist(REFERENCE_PARAMS, "dc")

        self.assertTrue(netlist.startswith("* CE amplifier\n"))
        for component in (
            "VCC NVCC 0 DC 12",
            "VIN NIN 0 DC 0 AC 0.01 SIN(0 0.01 1000)",
            "R1 NVCC NB 100000",
            "R2 NB 0 22000",
            "RC NVCC NC 2200",
            "RE NE 0 1000",
            "Q1 NC NB NE 0 QNPN",
            "CIN NIN NB 1e-05",
            "COUT NC NOUT 1e-05",
            "RL NOUT 0 10000",
            MODEL_DECLARATION,
            ".op",
            ".print op v(nvcc)",
            ".end",
        ):
            self.assertIn(component, netlist)
        self.assertEqual(netlist.count(".print"), 1)
        self.assertNotIn(".ac ", netlist)
        self.assertNotIn(".tran ", netlist)

    def test_ac_and_transient_netlists_use_expected_sweeps(self):
        ac = build_netlist(REFERENCE_PARAMS, "ac")
        tran = build_netlist(REFERENCE_PARAMS, "transient")

        self.assertIn(".ac dec 40 10 10Meg", ac)
        self.assertIn(".print ac vdb(nout) vp(nout)", ac)
        self.assertNotIn(".op", ac)
        self.assertIn(".tran 0.01m 5m", tran)
        self.assertIn(".print tran v(nin) v(nout)", tran)
        self.assertNotIn(".op", tran)
        self.assertEqual(ANALYSES, ("dc", "ac", "transient"))

    def test_unknown_analysis_is_rejected_before_a_netlist_is_built(self):
        with self.assertRaises(SpiceError):
            build_netlist(REFERENCE_PARAMS, "bogus")


class TestRunSimulationFailures(unittest.TestCase):
    def test_missing_engine_raises_spice_error(self):
        with patch("spice_engine.find_ngspice", return_value=None):
            with self.assertRaisesRegex(SpiceError, "ngspice"):
                run_simulation(REFERENCE_PARAMS, "dc", executable=None)

    def test_runner_uses_argument_list_without_shell_and_with_timeout(self):
        fake = FakeNgspice(OP_LOG)
        with patch("spice_engine.subprocess.run", side_effect=fake):
            result = run_simulation(
                REFERENCE_PARAMS, "dc", executable="ngspice-stub", timeout=17
            )

        self.assertEqual(fake.args[1:3], ["-b", "-o"])
        self.assertEqual(len(fake.args), 5)
        self.assertEqual(Path(fake.args[4]).name, "circuit.cir")
        self.assertNotIn("shell", fake.kwargs)
        self.assertEqual(fake.kwargs["timeout"], 17)
        self.assertTrue(fake.kwargs["capture_output"])
        self.assertFalse(Path(fake.args[3]).exists())  # temp cwd cleaned up
        self.assertEqual(result.analysis, "dc")
        self.assertAlmostEqual(result.op["nb"], 1.949112)
        self.assertIn(".end", result.netlist)

    def test_nonzero_exit_raises_spice_error(self):
        fake = FakeNgspice("Error: no data saved\n", returncode=1)
        with patch("spice_engine.subprocess.run", side_effect=fake):
            with self.assertRaisesRegex(SpiceError, "exit"):
                run_simulation(
                    REFERENCE_PARAMS, "dc", executable="ngspice-stub"
                )

    def test_empty_log_raises_spice_error(self):
        fake = FakeNgspice("")
        with patch("spice_engine.subprocess.run", side_effect=fake):
            with self.assertRaisesRegex(SpiceError, "empty"):
                run_simulation(
                    REFERENCE_PARAMS, "dc", executable="ngspice-stub"
                )

    def test_log_without_a_parsable_table_raises_spice_error(self):
        fake = FakeNgspice("Circuit: * CE amplifier\nWarning: weird line\n")
        with patch("spice_engine.subprocess.run", side_effect=fake):
            with self.assertRaisesRegex(SpiceError, "parse"):
                run_simulation(
                    REFERENCE_PARAMS, "dc", executable="ngspice-stub"
                )

    def test_timeout_raises_spice_error(self):
        timeout = subprocess.TimeoutExpired(["ngspice"], 30)
        fake = FakeNgspice("", exception=timeout)
        with patch("spice_engine.subprocess.run", side_effect=fake):
            with self.assertRaisesRegex(SpiceError, "timed out"):
                run_simulation(
                    REFERENCE_PARAMS, "dc", executable="ngspice-stub"
                )

    def test_incomplete_dc_node_table_raises_spice_error(self):
        partial = "\tnb\t1.949112e+00\n\tne\t1.289454e+00\n"
        fake = FakeNgspice(partial)
        with patch("spice_engine.subprocess.run", side_effect=fake):
            with self.assertRaisesRegex(SpiceError, "parse"):
                run_simulation(
                    REFERENCE_PARAMS, "dc", executable="ngspice-stub"
                )

    def test_truncated_ac_sweep_raises_spice_error(self):
        # AC_LOG ends at 10 kHz instead of the netlist's 10 MHz stop.
        fake = FakeNgspice(AC_LOG)
        with patch("spice_engine.subprocess.run", side_effect=fake):
            with self.assertRaisesRegex(SpiceError, "incomplete"):
                run_simulation(
                    REFERENCE_PARAMS, "ac", executable="ngspice-stub"
                )

    def test_truncated_transient_sweep_raises_spice_error(self):
        # TRAN_LOG ends at 1 ms instead of the netlist's 5 ms stop.
        fake = FakeNgspice(TRAN_LOG)
        with patch("spice_engine.subprocess.run", side_effect=fake):
            with self.assertRaisesRegex(SpiceError, "incomplete"):
                run_simulation(
                    REFERENCE_PARAMS, "transient", executable="ngspice-stub"
                )

    def test_non_monotonic_ac_index_and_frequency_raise_spice_error(self):
        bad_index = AC_LOG_COMPLETE.replace(
            "120\t1.000000e+07", "80\t1.000000e+07"
        )
        bad_frequency = AC_LOG_COMPLETE.replace(
            "120\t1.000000e+07", "120\t1.000000e+03"
        )
        for log in (bad_index, bad_frequency):
            with patch(
                "spice_engine.subprocess.run", side_effect=FakeNgspice(log)
            ):
                with self.assertRaisesRegex(SpiceError, "incomplete"):
                    run_simulation(
                        REFERENCE_PARAMS, "ac", executable="ngspice-stub"
                    )

    def test_non_monotonic_transient_index_and_time_raise_spice_error(self):
        bad_index = TRAN_LOG_COMPLETE.replace("3\t5.000000e-03", "2\t5.000000e-03")
        bad_time = TRAN_LOG_COMPLETE.replace("3\t5.000000e-03", "3\t1.000000e-04")
        for log in (bad_index, bad_time):
            with patch(
                "spice_engine.subprocess.run", side_effect=FakeNgspice(log)
            ):
                with self.assertRaisesRegex(SpiceError, "incomplete"):
                    run_simulation(
                        REFERENCE_PARAMS, "transient", executable="ngspice-stub"
                    )


class TestAcSummaryCrossings(unittest.TestCase):
    def test_finds_first_cutoff_on_rising_low_frequency_edge(self):
        rows = parse_ac_log(
            "0\t1.000000e+01\t-6.000000e+01\t0.000000e+00\n"
            "1\t1.000000e+02\t-4.000000e+01\t0.000000e+00\n"
            "2\t1.000000e+03\t-4.000000e+01\t0.000000e+00\n"
            "3\t1.000000e+04\t-6.000000e+01\t0.000000e+00\n"
        )

        self.assertAlmostEqual(
            _ac_summary(rows, REFERENCE_PARAMS)["f3db_hz"], 70.7946, delta=0.01
        )

    def test_finds_rising_cutoff_when_no_falling_edge_exists(self):
        rows = parse_ac_log(
            "0\t1.000000e+01\t-6.000000e+01\t0.000000e+00\n"
            "1\t1.000000e+02\t-5.000000e+01\t0.000000e+00\n"
            "2\t1.000000e+03\t-4.000000e+01\t0.000000e+00\n"
        )

        f3db = _ac_summary(rows, REFERENCE_PARAMS)["f3db_hz"]
        self.assertIsNotNone(f3db)
        self.assertAlmostEqual(f3db, 501.1872, delta=0.01)


class TestSimulationSummary(unittest.TestCase):
    def test_dc_summary_uses_ngspice_nodes_and_derived_ic(self):
        fake = FakeNgspice(OP_LOG)
        with patch("spice_engine.subprocess.run", side_effect=fake):
            result = run_simulation(
                REFERENCE_PARAMS, "dc", executable="ngspice-stub"
            )

        s = result.summary
        self.assertAlmostEqual(s["vcc"], 12.0)
        self.assertAlmostEqual(s["vb"], 1.949112)
        self.assertAlmostEqual(s["ve"], 1.289454)
        self.assertAlmostEqual(s["vc"], 9.189410)
        self.assertAlmostEqual(s["vce"], 7.899956, delta=1e-6)
        self.assertAlmostEqual(s["ic_ma"], 1.277541, delta=1e-5)

    def test_ac_summary_references_source_amplitude_and_missing_cutoff(self):
        fake = FakeNgspice(AC_LOG_COMPLETE)
        with patch("spice_engine.subprocess.run", side_effect=fake):
            result = run_simulation(
                REFERENCE_PARAMS, "ac", executable="ngspice-stub"
            )

        s = result.summary
        self.assertAlmostEqual(s["source_amplitude_v"], 0.01)
        # Fixture is -60.9999 dBV from a 10 mV source: -60.9999 - (-40) dB.
        self.assertAlmostEqual(s["midband_gain_db"], -20.9999, delta=0.01)
        # Every row (including the 10 MHz endpoint) stays above the -63.9999
        # dBV target, so no -3 dB crossing exists in either direction.
        self.assertIsNone(s["f3db_hz"])
        self.assertAlmostEqual(s["phase_deg"], 0.0577, delta=0.001)

    def test_transient_summary_uses_complete_sweep(self):
        fake = FakeNgspice(TRAN_LOG_COMPLETE)
        with patch("spice_engine.subprocess.run", side_effect=fake):
            result = run_simulation(
                REFERENCE_PARAMS, "transient", executable="ngspice-stub"
            )

        self.assertAlmostEqual(result.summary["peak_vin_v"], 0.01)
        self.assertAlmostEqual(result.summary["peak_vout_v"], 0.0486)


@unittest.skipIf(find_ngspice() is None, "ngspice is not installed")
class TestRealNgspiceSmoke(unittest.TestCase):
    def test_real_dc_run_returns_finite_bias_values(self):
        result = run_simulation(REFERENCE_PARAMS, "dc", timeout=30)

        self.assertTrue(all(math.isfinite(v) for v in result.op.values()))
        self.assertEqual(set(result.op), {"nvcc", "nb", "ne", "nc"})
        self.assertGreater(result.summary["ic_ma"], 0)
        self.assertGreater(result.summary["vce"], 0)

    def test_real_ac_run_returns_sweep_with_inverting_midband_phase(self):
        result = run_simulation(REFERENCE_PARAMS, "ac", timeout=30)

        self.assertGreater(len(result.ac), 100)
        midband = min(
            result.ac, key=lambda row: abs(row["frequency_hz"] - 1000.0)
        )
        self.assertLess(midband["phase_deg"], -90)
        self.assertTrue(math.isfinite(result.summary["midband_gain_db"]))

    def test_real_transient_run_returns_finite_inverted_waveforms(self):
        result = run_simulation(REFERENCE_PARAMS, "transient", timeout=30)

        self.assertGreater(len(result.tran), 100)
        peak = max(result.tran, key=lambda row: row["vin_v"])
        self.assertLess(peak["vout_v"], peak["vin_v"])
        self.assertTrue(math.isfinite(result.summary["peak_vin_v"]))


if __name__ == "__main__":
    unittest.main()
