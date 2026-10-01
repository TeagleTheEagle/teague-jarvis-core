"""Read-only process/trace census; no UAC or observer launch."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'code'))
import failure_preserve_v1 as f
value=f.host_census(ROOT)
output=ROOT/sys.argv[1]
if output.parent!=ROOT or output.exists():raise ValueError('EXCLUSIVE_LOCAL_REPORT_REQUIRED')
f.write_new(output,value)
print(json.dumps(dict(available=value['available'],processes=value['processes'],traces=value['traces'],unknown=value['unknown'],error=value.get('error'))))
if not f.census_clean(value,ROOT):sys.exit(1)
