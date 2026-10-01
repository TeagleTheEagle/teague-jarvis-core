"""Load candidate in test process only; all app fixtures use temporary data."""
from pathlib import Path
import importlib.util
import sys
import unittest
root=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(root/'review/inspection-candidate'),str(root)]
import server
server.ROOT=root
suite=unittest.defaultTestLoader.discover(str(root),pattern='test_*.py')
result=unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(not result.wasSuccessful())
