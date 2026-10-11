import io
import os
import socket
import unittest
import urllib.error
from unittest.mock import patch
import providers
import actions

class DiagnosticsTests(unittest.TestCase):
    def test_dns_error_labels_service_without_secret(self):
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError(socket.gaierror('private detail'))):
            with self.assertRaises(providers.ProviderError) as caught:
                providers.request('https://serpapi.com/search.json?api_key=secret')
        self.assertIn('DNS lookup failed', str(caught.exception))
        self.assertIn('SerpApi', str(caught.exception))
        self.assertNotIn('secret', str(caught.exception))
        self.assertNotIn('private detail', str(caught.exception))

    def test_auth_error_labels_voice(self):
        error=urllib.error.HTTPError('https://api.fish.audio/v1/tts',401,'',{},io.BytesIO(b'secret'))
        with patch('urllib.request.urlopen',side_effect=error):
            with self.assertRaises(providers.ProviderError) as caught:
                providers.request('https://api.fish.audio/v1/tts')
        self.assertIn('Fish Audio voice synthesis: Authentication failed',str(caught.exception))
        self.assertNotIn('secret',str(caught.exception))

    def test_serpapi_filters_unsafe_links(self):
        with patch.dict(os.environ,{'SERPAPI_API_KEY':'test'}), patch('actions.request',return_value={'organic_results':[{'title':'bad','link':'javascript:x'},{'title':'Good','link':'https://example.com','snippet':'Text'}]}):
            self.assertEqual(actions.search('test')['results'],[{'title':'Good','url':'https://example.com','description':'Text'}])

    def test_openai_preserves_tool_call(self):
        import threading
        call={'id':'call1','type':'function','function':{'name':'time_now','arguments':'{}'}}
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test','JARVIS_PROVIDER':'openai','OPENAI_MODEL':'gpt-4o-mini'}), patch('providers.request',return_value={'choices':[{'message':{'content':None,'tool_calls':[call]}}]}):
            result=providers.chat([],[],lambda *a: None,threading.Event())
        self.assertEqual(result['tool_calls'],[call])
