import tempfile
import unittest
from server import App, Run

class NavigationTests(unittest.TestCase):
    def test_navigation_result_and_event(self):
        with tempfile.TemporaryDirectory() as folder:
            app=App(folder)
            result=app.tool('navigate_panel',{'panel':'projects'})
            self.assertEqual(result,{'panel':'projects','status':'navigation_requested'})
            self.assertEqual(app.tool('navigate_panel',{'panel':'screen_vision'})['panel'],'screen_vision')
            for args in ({'panel':'https://example.com'},{'panel':'projects','command':'delete'},{}):
                with self.assertRaises(ValueError):app.tool('navigate_panel',args)
