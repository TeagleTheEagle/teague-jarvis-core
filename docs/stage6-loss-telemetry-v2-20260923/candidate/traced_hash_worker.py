"""Delegate unchanged hash worker, adding only a diagnostic entry/return sidecar."""
import time
ENTRY_NS=time.perf_counter_ns()
import sys,runpy
from workspace import CODE,run_dir,activate_temp
from integration_marks import Marks
root=run_dir(sys.argv[1]);activate_temp(root)
case=sys.argv[2];assert case in ('normal','hash-start-failure')
marks=Marks(root,'hash-worker',ENTRY_NS);status='EXCEPTION'
try:
 marks.add('HELPER_INVOCATION',helper='baseline_hash_worker.py')
 if case=='hash-start-failure':raise RuntimeError('CONTROLLED_HASH_START_FAILURE')
 sys.argv=[str(CODE/'baseline_hash_worker.py'),root.name]
 runpy.run_path(str(CODE/'baseline_hash_worker.py'),run_name='__main__')
 status='RETURNED';marks.add('HELPER_RETURN',helper='baseline_hash_worker.py',exitCode=0)
except SystemExit as exc:
 status='RETURNED' if exc.code in (None,0) else 'FAILED'
 marks.add('HELPER_RETURN',helper='baseline_hash_worker.py',exitCode=exc.code)
 raise
except BaseException as exc:
 marks.add('EXCEPTION',exceptionType=type(exc).__name__,controlled=case=='hash-start-failure')
 raise
finally:marks.close(status)
