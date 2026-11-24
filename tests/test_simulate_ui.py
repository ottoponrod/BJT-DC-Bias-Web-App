"""Markup tests for the Lab 04 simulation panel (Task 3)."""

import unittest
from unittest.mock import patch

from app import app
from spice_engine import MODEL_NAME, SpiceError, find_ngspice


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


class SimulationMarkupTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_has_namespaced_simulation_form_and_engine_badge(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        for name in (
            b'name="sim_analysis"', b'name="sim_vcc"', b'name="sim_r1"',
            b'name="sim_rl"', b'name="sim_cin"', b'name="sim_cout"',
            b'name="sim_amplitude"', b'name="sim_frequency"',
            b'name="sim_unit"',
        ):
            self.assertIn(name, response.data)
        self.assertIn(b"Run Simulation", response.data)
        self.assertIn(b'id="sim-status"', response.data)
        self.assertIn(MODEL_NAME.encode(), response.data)
        self.assertIn(b"Analytical (Lab 03)", response.data)

    @unittest.skipIf(find_ngspice() is None, "ngspice is not installed")
    def test_dc_result_markup_labels_every_value_as_ngspice_op(self):
        response = self.client.post("/simulate", data=VALID_SIM)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-sim-state="success"', response.data)
        self.assertIn(b"ngspice .op", response.data)
        self.assertIn(b'id="spice-vb"', response.data)
        self.assertIn(b'id="spice-ve"', response.data)
        self.assertIn(b'id="spice-vc"', response.data)
        self.assertIn(b'id="spice-vce"', response.data)
        self.assertIn(b'id="spice-ic"', response.data)
        self.assertIn(b"mA", response.data)
        self.assertIn(MODEL_NAME.encode(), response.data)

    @unittest.skipIf(find_ngspice() is None, "ngspice is not installed")
    def test_ac_result_markup_has_bode_axes_units_and_cutoff_status(self):
        response = self.client.post(
            "/simulate", data={**VALID_SIM, "sim_analysis": "ac"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-sim-state="success"', response.data)
        self.assertIn(b"frequency (Hz)", response.data)
        self.assertIn(b"gain (dB)", response.data)
        self.assertIn(b"phase (deg)", response.data)
        self.assertIn(b"<polyline", response.data)
        self.assertIn(b'id="spice-cutoff"', response.data)
        self.assertTrue(
            b"not determined in sweep range" in response.data
            or b"-3 dB" in response.data
        )

    @unittest.skipIf(find_ngspice() is None, "ngspice is not installed")
    def test_transient_markup_has_time_ms_axis_and_waveform_legend(self):
        response = self.client.post(
            "/simulate", data={**VALID_SIM, "sim_analysis": "transient"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'time (ms)', response.data)
        self.assertIn(b"Vin [V]", response.data)
        self.assertIn(b"Vout [V]", response.data)
        self.assertIn(b"<polyline", response.data)

    def test_engine_error_shows_error_state_without_any_plot_or_values(self):
        with patch("app.run_simulation", side_effect=SpiceError("engine failed")):
            response = self.client.post("/simulate", data=VALID_SIM)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-sim-state="error"', response.data)
        self.assertIn(b"SPICE", response.data)
        self.assertNotIn(b"<polyline", response.data)
        self.assertNotIn(b"ngspice .op", response.data)
        self.assertNotIn(b'data-sim-state="success"', response.data)


if __name__ == "__main__":
    unittest.main()
