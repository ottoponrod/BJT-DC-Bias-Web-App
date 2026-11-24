"""Tests for the separate /simulate route (Task 2)."""

import unittest
from contextlib import contextmanager
from unittest.mock import patch

from flask import template_rendered

from app import SIM_DEFAULTS, app
from spice_engine import (
    MODEL_NAME,
    SimulationResult,
    SpiceError,
    SpiceParams,
    find_ngspice,
)


VALID_SIM = {
    "sim_vcc": "12",
    "sim_r1": "100",
    "sim_r2": "22",
    "sim_rc": "2.2",
    "sim_re": "1",
    "sim_rl": "10",
    "sim_cin": "10",
    "sim_cout": "10",
    "sim_amplitude": "10",
    "sim_frequency": "1",
    "sim_unit": "kilo",
    "sim_analysis": "dc",
}


@contextmanager
def rendered_contexts():
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append(context)

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


class SimulateRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_index_supplies_simulation_form_defaults(self):
        with rendered_contexts() as contexts:
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        ctx = contexts[-1]
        self.assertEqual(ctx["sim_form"]["vcc"], SIM_DEFAULTS["vcc"])
        self.assertEqual(ctx["sim_form"]["amplitude"], "10")
        self.assertIsNone(ctx["sim_result"])
        self.assertIsNone(ctx["sim_error"])
        self.assertIn("ngspice", ctx["sim_status"])
        self.assertIn(MODEL_NAME, ctx["sim_status"])

    @unittest.skipIf(find_ngspice() is None, "ngspice is not installed")
    def test_dc_post_returns_real_spice_bias_values_and_status(self):
        with rendered_contexts() as contexts:
            response = self.client.post("/simulate", data=VALID_SIM)

        self.assertEqual(response.status_code, 200)
        ctx = contexts[-1]
        self.assertIsNone(ctx["sim_error"])
        self.assertEqual(ctx["analysis"], "dc")
        self.assertEqual(ctx["sim_result"].analysis, "dc")
        s = ctx["sim_result"].summary
        self.assertAlmostEqual(s["vb"], 1.949, delta=0.02)
        self.assertAlmostEqual(s["ve"], 1.289, delta=0.02)
        self.assertAlmostEqual(s["vc"], 9.189, delta=0.05)
        self.assertAlmostEqual(s["vce"], 7.900, delta=0.05)
        self.assertAlmostEqual(s["ic_ma"], 1.278, delta=0.02)
        self.assertIn("success", ctx["sim_status"])
        self.assertIn(MODEL_NAME, ctx["sim_status"])

    def test_zero_emitter_resistor_is_rejected_before_running(self):
        with rendered_contexts() as contexts:
            response = self.client.post(
                "/simulate", data={**VALID_SIM, "sim_re": "0"}
            )

        self.assertEqual(response.status_code, 200)
        ctx = contexts[-1]
        self.assertIsNone(ctx["sim_result"])
        self.assertIn("ความต้านทาน", ctx["sim_error"])

    def test_non_numeric_amplitude_is_rejected_before_running(self):
        with rendered_contexts() as contexts:
            response = self.client.post(
                "/simulate", data={**VALID_SIM, "sim_amplitude": "abc"}
            )

        self.assertEqual(response.status_code, 200)
        ctx = contexts[-1]
        self.assertIsNone(ctx["sim_result"])
        self.assertIn("ตัวเลข", ctx["sim_error"])

    def test_unknown_analysis_is_rejected(self):
        with rendered_contexts() as contexts:
            response = self.client.post(
                "/simulate", data={**VALID_SIM, "sim_analysis": "bogus"}
            )

        self.assertEqual(response.status_code, 200)
        ctx = contexts[-1]
        self.assertIsNone(ctx["sim_result"])
        self.assertIn("โหมด", ctx["sim_error"])

    def test_runner_receives_typed_si_params_not_raw_form_strings(self):
        fake = SimulationResult(
            analysis="dc", model=MODEL_NAME, netlist="", log_excerpt=""
        )
        with patch("app.run_simulation", return_value=fake) as runner:
            with rendered_contexts() as contexts:
                response = self.client.post("/simulate", data=VALID_SIM)

        self.assertEqual(response.status_code, 200)
        params, analysis = runner.call_args.args
        self.assertIsInstance(params, SpiceParams)
        self.assertEqual(analysis, "dc")
        self.assertAlmostEqual(params.r1_ohm, 100_000.0)
        self.assertAlmostEqual(params.cin_f, 10e-6)
        self.assertAlmostEqual(params.amplitude_v, 0.01)
        self.assertAlmostEqual(params.frequency_hz, 1000.0)
        self.assertEqual(contexts[-1]["sim_result"], fake)

    def test_spice_error_returns_200_without_success_text(self):
        with patch("app.run_simulation", side_effect=SpiceError("ngspice crashed")):
            with rendered_contexts() as contexts:
                response = self.client.post("/simulate", data=VALID_SIM)

        self.assertEqual(response.status_code, 200)
        ctx = contexts[-1]
        self.assertIsNone(ctx["sim_result"])
        self.assertIn("ล้มเหลว", ctx["sim_error"])
        self.assertIn("failed", ctx["sim_status"])
        self.assertNotIn(b"run: success", response.data)


if __name__ == "__main__":
    unittest.main()
