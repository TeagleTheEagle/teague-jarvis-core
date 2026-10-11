import unittest
from shadow_report import summarize


class ReportTests(unittest.TestCase):
    def test_errors_not_counted_as_agreement(self):
        rows = [dict(schema_valid=True, match=True, latency_ms=100, lifecycle='cold'),
                dict(schema_valid=True, match=False, latency_ms=200, lifecycle='warm'),
                dict(schema_valid=False, match=None, error='timeout'),
                dict(schema_valid=False, match=None, error='unknown_intent')]
        result = summarize(rows)
        self.assertEqual(result['agreement_rate'], .5)
        self.assertEqual(result['total_shadow_requests'], 4)
        self.assertEqual(result['timeouts'], 1)
        self.assertEqual(result['schema_failures'], 1)
        self.assertEqual(result['average_latency_ms'], 150)
        self.assertEqual(result['p95_latency_ms'], 200)
        self.assertEqual(result['cold_latency_ms'], 100)
        self.assertIsNone(summarize([])['agreement_rate'])
