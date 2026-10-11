"""Pure contract tests; no app, browser, user database or network."""
import unittest
from inspection_contract_candidate import PANELS, new_evidence, tool_schema, validate_request


class ContractTests(unittest.TestCase):
    def test_all_supported_panels(self):
        for panel in PANELS:
            self.assertEqual(validate_request({'panel': panel})['panel'], panel)

    def test_defaults(self):
        self.assertEqual(validate_request({'panel': 'command'}),
                         {'panel': 'command', 'scope': 'viewport', 'focus': ''})

    def test_full_panel_request_is_not_proof_of_coverage(self):
        evidence = new_evidence({'panel': 'communications', 'scope': 'full_panel'})
        self.assertEqual(evidence['coverage'], 'none')
        self.assertIsNone(evidence['verified_panel'])
        self.assertTrue(all(s == 'not_attempted' for s in evidence['stages'].values()))
        self.assertEqual(evidence['screenshots'], [])

    def test_arbitrary_destinations_rejected(self):
        for panel in ('https://example.com', '../settings', 'screen_vision', 'all', '', None, []):
            with self.subTest(panel=panel), self.assertRaises(ValueError):
                validate_request({'panel': panel})

    def test_extra_controls_rejected(self):
        for field in ('url', 'javascript', 'shell', 'path', 'clicks', 'consent'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_request({'panel': 'command', field: 'anything'})

    def test_invalid_shapes(self):
        for value in (None, [], 'command', {}, {'panel': 'command', 'scope': []},
                      {'panel': 'command', 'scope': 'entire_screen'},
                      {'panel': 'command', 'focus': {}},
                      {'panel': 'command', 'focus': 'a' * 2001}):
            with self.subTest(value=type(value).__name__), self.assertRaises(ValueError):
                validate_request(value)

    def test_schema_has_no_unbounded_controls(self):
        schema = tool_schema()['function']['parameters']
        self.assertFalse(schema['additionalProperties'])
        self.assertEqual(set(schema['properties']), {'panel', 'scope', 'focus'})
        self.assertEqual(schema['properties']['panel']['enum'], list(PANELS))

    def test_evidence_independent_between_requests(self):
        one = new_evidence({'panel': 'command'})
        two = new_evidence({'panel': 'command'})
        one['errors'].append('test')
        self.assertEqual(two['errors'], [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
