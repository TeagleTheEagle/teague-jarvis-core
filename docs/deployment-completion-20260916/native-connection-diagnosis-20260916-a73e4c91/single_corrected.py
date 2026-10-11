from pathlib import Path
import sys
R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'tests/lifecycle_stage4'))
from fixtures import native_probe
native_probe(('correct',))
