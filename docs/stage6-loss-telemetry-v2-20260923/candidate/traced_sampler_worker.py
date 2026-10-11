import time
ENTRY_NS=time.perf_counter_ns()
import sys,runpy
from workspace import CODE,run_dir
from integration_marks import Marks
root=run_dir(sys.argv[1]);marks=Marks(root,'sampler',ENTRY_NS);status='EXCEPTION'
try:
 marks.add('WORK_BEGIN');sys.argv[0]=str(CODE/'sampler_worker.py')
 runpy.run_path(sys.argv[0],run_name='__main__');marks.add('WORK_END');status='RETURNED'
except BaseException as exc:marks.add('EXCEPTION',exceptionType=type(exc).__name__);raise
finally:marks.close(status)
