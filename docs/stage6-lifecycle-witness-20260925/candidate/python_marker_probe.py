import time
ENTRY=time.perf_counter_ns()
import sys
from workspace import run_dir
from integration_marks import Marks
m=Marks(run_dir(sys.argv[1]),'smoke',ENTRY)
m.add('WORK_BEGIN')
print('preserved stdout')
m.add('WORK_END')
m.close('RETURNED')
