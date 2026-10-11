import unittest
from unittest.mock import patch
from voice_engine import VoiceEngine, prepare
import providers


class VoiceEngineTests(unittest.TestCase):
    def test_repeated_audio_reused_and_profile_separated(self):
        engine=VoiceEngine()
        with patch('providers.speech',return_value=b'a'*200) as speech:
            self.assertEqual(engine.synthesize('Hello.'),engine.synthesize('Hello.'))
            speech.assert_called_once()
            engine.synthesize('Hello.','fish')
            self.assertEqual(speech.call_count,2)

    def test_expired_and_over_budget_audio_not_reused(self):
        for engine in (VoiceEngine(ttl=0),VoiceEngine(max_bytes=100)):
            with patch('providers.speech',return_value=b'a'*200) as speech:
                engine.synthesize('Hello.');engine.synthesize('Hello.')
                self.assertEqual(speech.call_count,2)

    def test_failed_generation_not_cached(self):
        engine=VoiceEngine()
        with patch('providers.speech',side_effect=[b'',b'a'*200]) as speech:
            with self.assertRaises(providers.ProviderError):engine.synthesize('Hello.')
            engine.synthesize('Hello.')
            self.assertEqual(speech.call_count,2)

    def test_long_reply_ends_at_complete_sentence(self):
        sentence='This sentence is complete. '
        text=prepare(sentence*300)
        self.assertLess(len(text),4000)
        self.assertTrue(text.endswith('complete. The rest is available in the chat.'))
