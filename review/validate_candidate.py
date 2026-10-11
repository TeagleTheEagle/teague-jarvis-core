"""Load the proposed server only in this test process; never start a server."""
import importlib.util
import sys
import unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('server', root / 'review/server_candidate.py')
module = importlib.util.module_from_spec(spec)
sys.modules['server'] = module
spec.loader.exec_module(module)
# Candidate sits in review, but normal server resources still live at root.
module.ROOT = root
suite = unittest.defaultTestLoader.discover(str(root), pattern='test_*.py')
suite.addTests(unittest.defaultTestLoader.loadTestsFromName('review.briefing_regressions'))
result = unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(not result.wasSuccessful())
