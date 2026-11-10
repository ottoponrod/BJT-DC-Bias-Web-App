import unittest

from app import app

VALID = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1",
         "beta": "100", "vbe": "0.7", "unit": "kilo"}


class WebTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_returns_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="vcc"', response.data)
        self.assertIn(b'name="unit"', response.data)

    def test_calculate_renders_results(self):
        response = self.client.post("/calculate", data=VALID)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.230", response.data)
        self.assertIn(b"8.052", response.data)
        self.assertIn("Active".encode(), response.data)

    def test_invalid_input_shows_error_not_crash(self):
        response = self.client.post("/calculate", data={**VALID, "r1": "0"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("ต้องมากกว่า 0".encode(), response.data)

    def test_missing_form_data_shows_error(self):
        response = self.client.post("/calculate", data={})
        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอก".encode(), response.data)

    def test_non_numeric_input_shows_error(self):
        response = self.client.post("/calculate", data={**VALID, "vcc": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("ตัวเลข".encode(), response.data)

    def test_comma_separated_input_shows_error(self):
        response = self.client.post("/calculate", data={**VALID, "r1": "1,000"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("ตัวเลข".encode(), response.data)


    def test_page_links_stylesheet(self):
        response = self.client.get("/")
        self.assertIn(b"style.css", response.data)

    def test_results_show_units_and_warning(self):
        response = self.client.post("/calculate", data={**VALID, "re": "0.1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'class="region-banner"', response.data)
        self.assertIn(b'class="warning"', response.data)
        self.assertIn("Saturation".encode(), response.data)
        self.assertIn(b"mA", response.data)

    def test_active_region_shows_banner_with_reason(self):
        response = self.client.post("/calculate", data=VALID)
        self.assertIn(b'class="region-banner"', response.data)
        self.assertIn(b'data-region="active"', response.data)
        self.assertIn(b"Active region approximation OK", response.data)
        self.assertIn(b"8.052", response.data)


    def test_ohm_unit_is_honoured(self):
        response = self.client.post("/calculate", data={
            "vcc": "12", "r1": "100000", "r2": "22000", "rc": "2200",
            "re": "1000", "beta": "100", "vbe": "0.7", "unit": "ohm",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.230", response.data)
        self.assertIn(b"8.052", response.data)
        self.assertIn("Active".encode(), response.data)

    def test_nan_input_shows_error(self):
        response = self.client.post("/calculate", data={**VALID, "vcc": "nan"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("จำนวนจำกัด".encode(), response.data)

    def test_overflow_exponent_shows_error(self):
        response = self.client.post("/calculate", data={**VALID, "vcc": "1e400"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("จำนวนจำกัด".encode(), response.data)


    def test_page_has_header_and_goal_strip(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'class="site-header"', response.data)
        self.assertIn(b'class="goal-strip"', response.data)


if __name__ == "__main__":
    unittest.main()
