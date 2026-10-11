"""Exclusive new candidate successors. Does not execute any observer or campaign."""
import pathlib,json,shutil
R=pathlib.Path(__file__).resolve().parent
C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
def get(n):return (C/n).read_text()
def new(n,s):
 with (C/n).open('x',encoding='utf8',newline='\n') as f:f.write(s)
def rep(s,a,b):
 assert a in s,a
 return s.replace(a,b)
for n in ('coordination_v3.py','evidence_support_v3.py','terminal_receipt_v3.hpp'):shutil.copyfile(R/n,C/n)
s=get('small_binding_v2.py').replace('stage6-small-tracker-integration-v2','stage6-small-coordination-v3').replace('small-source-v2.json','small-source-v3.json').replace('small-declaration-v2.json','small-declaration-v3.json')
s=rep(s,"kernelCapture=180.0,channels=", "kernelCapture=180.0,cleanup=20.0,coordination='stage6-terminal-v3',channels=")
new('small_binding_v3.py',s)
s=get('large_collect.py').replace('from evidence_support import','from evidence_support_v3 import')
s=rep(s,"or not proof['allExited'] or not proof['allHandlesClosed']", "or not proof['localFinalized'] or not proof['allHandlesClosed']")
new('large_collect_v3.py',s)
s=get('traced_collect.py').replace('import large_collect as collector','import large_collect_v3 as collector')
s=rep(s,'finally:marks.close(status)',"finally:\n   marks.close(status)\n   if status=='RETURNED':\n    from evidence_support_v3 import publish_phase_a\n    publish_phase_a(root)")
new('traced_collect_v3.py',s)
# Preserve original bytes; the fixed native DLL path requires a narrow copied entry shim.
# This change is in the new candidate only; original candidate remains immutable.
(C/'traced_collect.py').write_text('''"""Versioned TEST collector entry shim; fixed native RunCollector entry."""
import sys
from workspace import run_dir,activate_temp
from traced_collect_v3 import main
if __name__=='__main__':
 root=run_dir(sys.argv[1]);activate_temp(root);sys.exit(main(root,sys.argv[2]))
''')
s=get('tracker_adapter_v2.py').replace('from small_binding_v2 import','from small_binding_v3 import').replace('small-declaration-v2.json','small-declaration-v3.json').replace('from support_verifier import','from support_verifier_v3 import')
s=rep(s,"  need(row['exitFiletime']==k['exitFiletime'] and row['exitCode']==k['exitCode'],'TRACKER_EXIT_CONTRADICTION')", "  if row['exitFiletime'] is not None:\n   need(row['exitFiletime']==k['exitFiletime'] and row['exitCode']==k['exitCode'],'TRACKER_EXIT_CONTRADICTION')\n  else:\n   need(row['eligibleConsoleHelper'] is True and row['closed'],'UNAPPROVED_PENDING')")
# Pending helper's external proof is mandatory; no synthesized local exit fields.
s=rep(s," need(identity(doc['anchor'])==collector,'ANCHOR_COLLECTOR')", " need(identity(doc['anchor'])==collector,'ANCHOR_COLLECTOR')\n from completed_v3 import verify_terminal\n verify_terminal(root,kernel)")
s=rep(s,"and h['exitFiletime']==k['exitFiletime'] and h['exitCode']==k['exitCode']", "and h['exitFiletime']==k['exitFiletime'] and h['exitCode']==k['exitCode']")
new('tracker_adapter_v3.py',s)
s=get('support_verifier.py').replace('stage6-independent-tree-support-v1','stage6-independent-tree-support-v3')
s=rep(s,"            require(type(row['exitFiletime']) is str and row['exitFiletime'].isdecimal()\n                    and int(row['exitFiletime']) >= int(key[1]), 'missing exit')\n            require(type(row['exitCode']) is int, 'missing exit code')", "            if row['exitFiletime'] is None:\n                require(row['eligibleConsoleHelper'] is True and row['parentPid']==anchor['pid'] and row['capture']['image'].lower()==r'c:\\windows\\system32\\conhost.exe', 'unapproved pending helper')\n                require(row['stateAtClose']==258 and row['exitCode'] is None, 'pending false exit')\n                number(row['localCloseQpc'])\n            else:\n                require(type(row['exitFiletime']) is str and row['exitFiletime'].isdecimal() and int(row['exitFiletime'])>=int(key[1]), 'missing exit')\n                require(type(row['exitCode']) is int, 'missing exit code')")
new('support_verifier_v3.py',s)
s=get('authority_trace.cpp')
s=rep(s,'static std::string List(', '#include "terminal_receipt_v3.hpp"\nstatic std::string List(')
s=rep(s,'LONGLONG begin=Q();bool requested=false;', 'LONGLONG begin=Q();bool requested=false;bool receiptPublished=false;')
s=rep(s,'Sample();if(GetFileAttributesW', '''Sample();if(!receiptPublished){try{
 if(GetFileAttributesW((folder+L"\\\\phase-a-v3.json").c_str())!=INVALID_FILE_ATTRIBUTES){
  ULONG queried=ControlTraceW(sessionHandle,session.c_str(),p,EVENT_TRACE_CONTROL_QUERY);
  if(queried||p->EventsLost||p->RealTimeBuffersLost||p->LogBuffersLost)throw std::runtime_error("terminal trace loss/query");
  receiptPublished=terminal_v3::WorkloadReceipt();
 }
 }catch(const std::exception&e){++faults;Write(L"terminal-failure-v3.json",std::string("{\\"error\\":")+J(e.what())+"}");break;}}
 if(GetFileAttributesW''')
new('authority_trace_v3.cpp',s)
print(str(C))
