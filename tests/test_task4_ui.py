"""Regression tests for the Task 4 UI-only polish."""

import unittest
from pathlib import Path

from app import app
from spice_engine import find_ngspice


ROOT = Path(__file__).resolve().parents[1]
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


class Task4MarkupTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_simulation_form_groups_related_inputs(self):
        html = self.client.get("/").data.decode("utf-8")

        for legend in (
            "Bias network",
            "Coupling capacitors",
            "Source &amp; sweep",
            "Units",
        ):
            self.assertIn(legend, html)
        self.assertIn('class="sim-group"', html)

    def test_simulation_inputs_declare_numeric_constraints(self):
        html = self.client.get("/").data.decode("utf-8")

        for field in ("vcc", "r1", "rl", "cin", "amplitude", "frequency"):
            marker = f'id="sim_{field}"'
            self.assertIn(marker, html)
            fragment = html[html.index(marker):html.index(marker) + 180]
            self.assertIn('type="number"', fragment)
            self.assertIn('min="', fragment)
            self.assertIn("required", fragment)

    def test_status_is_announced_and_results_start_not_busy(self):
        html = self.client.get("/").data.decode("utf-8")

        self.assertIn('id="sim-status"', html)
        status = html[html.index('id="sim-status"'):html.index('id="sim-status"') + 160]
        self.assertIn('role="status"', status)
        self.assertIn('aria-live="polite"', status)
        self.assertIn('class="sim-status"', status)
        self.assertIn('aria-busy="false"', html)

    def test_analytical_heading_no_longer_wraps_mode_label_into_it(self):
        html = self.client.get("/").data.decode("utf-8")

        self.assertIn("<h2>ผลลัพธ์ DC Bias</h2>", html)
        self.assertIn('class="result-mode"', html)

    def test_footer_states_both_labs_and_keeps_assignment_context(self):
        html = self.client.get("/").data.decode("utf-8")

        self.assertIn("Lab 03", html.split("<footer")[1])
        self.assertIn("Lab 04", html.split("<footer")[1])
        self.assertIn("Assignment context", html)

    @unittest.skipIf(find_ngspice() is None, "ngspice is not installed")
    def test_ac_and_transient_plots_are_scrollable(self):
        for analysis in ("ac", "transient"):
            with self.subTest(analysis=analysis):
                html = self.client.post(
                    "/simulate", data={**VALID_SIM, "sim_analysis": analysis}
                ).data.decode("utf-8")
                self.assertIn('class="plot-scroll"', html)
                self.assertIn("Scroll horizontally", html)


class Task4SourceTests(unittest.TestCase):
    def test_pending_handler_disables_button_without_faking_results(self):
        script = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

        self.assertIn("Running ngspice", script)
        self.assertIn("dataset.pending", script)
        self.assertIn("aria-busy", script)
        self.assertIn("pageshow", script)
        self.assertNotIn("innerHTML", script)

    def test_css_fixes_intermediate_layout_and_status_border(self):
        css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

        self.assertIn("@media (max-width: 1099px)", css)
        self.assertIn(".layout > .card:first-child", css)
        self.assertIn("min-width: 640px", css)
        status_rule = css[css.index(".sim-status {"):css.index(".sim-status[data-state=")]
        self.assertNotIn("border-left", status_rule)


if __name__ == "__main__":
    unittest.main()
