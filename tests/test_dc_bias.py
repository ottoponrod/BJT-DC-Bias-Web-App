import math
import unittest

from dc_bias import BiasInputs, ValidationError, calculate_dc_bias

SAMPLE = dict(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
              re=1_000.0, beta=100.0, vbe=0.70)


class ActiveRegionTests(unittest.TestCase):
    def test_reference_values(self):
        result = calculate_dc_bias(BiasInputs(**SAMPLE))
        self.assertEqual(result.region, "active")
        self.assertAlmostEqual(result.vth, 2.1639, places=3)
        self.assertAlmostEqual(result.ib * 1e6, 12.2986, places=2)
        self.assertAlmostEqual(result.ic * 1e3, 1.2299, places=3)
        self.assertAlmostEqual(result.ie * 1e3, 1.2422, places=3)
        self.assertAlmostEqual(result.ve, 1.2422, places=3)
        self.assertAlmostEqual(result.vb, 1.9422, places=3)
        self.assertAlmostEqual(result.vc, 9.2943, places=3)
        self.assertAlmostEqual(result.vce, 8.0522, places=3)


class ValidationTests(unittest.TestCase):
    def assert_rejected(self, **overrides):
        with self.assertRaises(ValidationError):
            calculate_dc_bias(BiasInputs(**{**SAMPLE, **overrides}))

    def test_rejects_zero_or_negative_resistance(self):
        for field in ("r1", "r2", "rc", "re"):
            self.assert_rejected(**{field: 0.0})
            self.assert_rejected(**{field: -1.0})

    def test_rejects_nonpositive_beta(self):
        self.assert_rejected(beta=0.0)
        self.assert_rejected(beta=-50.0)

    def test_rejects_nonpositive_vcc(self):
        self.assert_rejected(vcc=0.0)
        self.assert_rejected(vcc=-12.0)

    def test_rejects_vbe_outside_range(self):
        self.assert_rejected(vbe=0.0)
        self.assert_rejected(vbe=-0.7)
        self.assert_rejected(vbe=12.0)
        self.assert_rejected(vbe=15.0)

    def test_error_message_is_thai_and_specific(self):
        with self.assertRaises(ValidationError) as ctx:
            calculate_dc_bias(BiasInputs(**{**SAMPLE, "r1": 0.0}))
        self.assertIn("ต้องมากกว่า 0", str(ctx.exception))


class RegionTests(unittest.TestCase):
    def test_cutoff_returns_off_state(self):
        result = calculate_dc_bias(BiasInputs(
            vcc=5.0, r1=100_000.0, r2=10_000.0, rc=2_200.0,
            re=1_000.0, beta=100.0, vbe=0.70))
        self.assertEqual(result.region, "cutoff")
        self.assertEqual(result.ib, 0.0)
        self.assertEqual(result.ic, 0.0)
        self.assertEqual(result.ie, 0.0)
        self.assertAlmostEqual(result.ve, 0.0)
        self.assertAlmostEqual(result.vb, result.vth)
        self.assertAlmostEqual(result.vc, 5.0)
        self.assertAlmostEqual(result.vce, 5.0)
        self.assertTrue(result.warnings)

    def test_cutoff_boundary_vth_equals_vbe(self):
        vcc, r1, r2 = 7.0, 100_000.0, 10_000.0
        vth = vcc * r2 / (r1 + r2)
        result = calculate_dc_bias(BiasInputs(
            vcc=vcc, r1=r1, r2=r2, rc=2_200.0,
            re=1_000.0, beta=100.0, vbe=vth))
        self.assertEqual(result.region, "cutoff")

    def test_saturation_when_vce_negative_low(self):
        result = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
            re=100.0, beta=100.0, vbe=0.70))
        self.assertEqual(result.region, "saturation")
        self.assertTrue(result.warnings)

    def test_near_saturation_band(self):
        result = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_100.0,
            re=100.0, beta=100.0, vbe=0.70))
        self.assertEqual(result.region, "near-saturation")
        self.assertTrue(result.warnings)

    def test_active_has_no_warning(self):
        result = calculate_dc_bias(BiasInputs(**SAMPLE))
        self.assertEqual(result.warnings, [])

    def test_extreme_values_stay_finite(self):
        result = calculate_dc_bias(BiasInputs(
            vcc=1000.0, r1=1e9, r2=1e9, rc=1e9, re=1e9,
            beta=1e6, vbe=0.70))
        for value in (result.vth, result.rth, result.ib, result.ic, result.ie,
                      result.vb, result.ve, result.vc, result.vce):
            self.assertTrue(math.isfinite(value))

    def test_rejects_non_finite_inputs(self):
        for field in ("vcc", "r1", "beta", "vbe"):
            for bad in (float("nan"), float("inf")):
                with self.assertRaises(ValidationError):
                    calculate_dc_bias(
                        BiasInputs(**{**SAMPLE, field: bad}))


if __name__ == "__main__":
    unittest.main()
