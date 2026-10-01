import unittest
import providers


class SpeechPolishTests(unittest.TestCase):
    def test_pronunciation_and_measurements(self):
        self.assertEqual(providers.speech_text('Mr. Teague, the GPS API took 250 ms over 12 km.'),
                         'Mister Teague, the G P S A P I took 250 milliseconds over 12 kilometres.')

    def test_numbers_and_links_preserved(self):
        spoken = providers.speech_text('**18%** of 250 is 45. [Details](https://example.com)')
        self.assertIn('18 percent of 250 is 45.', spoken)
        self.assertNotIn('https', spoken)
        self.assertNotIn('**', spoken)

    def test_code_is_not_read_aloud(self):
        spoken = providers.speech_text('Here is the example.\n```python\nprint(123)\n```')
        self.assertNotIn('print', spoken)
        self.assertIn('Code is shown on screen.', spoken)
