"""Prepare a new TEST successor only. Does not launch observers or a collector."""
import pathlib,json,hashlib,shutil,subprocess,difflib
R=pathlib.Path(__file__).parent;cfg=json.loads((R/'before.json').read_text());C=pathlib.Path(cfg['candidate']);N=pathlib.Path(cfg['predecessor'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,s):
 with (C/n).open('x',encoding='utf8',newline='') as f:f.write(s)
def replace(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
for name in ('workspace_binding_v4.py','evidence_format_v4.py','candidate_dll_v4.ps1'):shutil.copy2(R/name,C/name)
allow=dict(syntheticRoots=[str(C/'small-synthetic')],approvedProtectedRoots=[],realProtectedAccess=False)
(C/'baseline-allowlist.json').write_text(json.dumps(allow,indent=2))
s=(N/'small_launch_v3.ps1').read_text();a=s.index("Add-Type -TypeDefinition @'");b=s.index("'@",a)+2
s=s[:a]+". (Join-Path $PSScriptRoot 'candidate_dll_v4.ps1')\nInitialize-J6CandidateBridge\n"+s[b:]
s=replace(s,"$case=(Get-Content", "& $py -B (Join-Path $PSScriptRoot 'workspace_binding_v4.py') verify $Run\nif($LASTEXITCODE -ne 0){throw 'Workspace binding failed'}\n$case=(Get-Content")
s=replace(s,"$root=Get-LiveRun $Run;Set-LiveTemp $root","$root=Get-LiveRun $Run;Set-LiveTemp $root\n. (Join-Path $PSScriptRoot 'runtime_scope_v4.ps1');Set-J6RuntimeScope")
put('small_launch_v4.ps1',s)
s=(N/'external_driver_v3.py').read_text().replace("CODE/'small_launch_v3.ps1'","CODE/'small_launch_v4.ps1'")
s=replace(s,"from small_binding_v3 import validate","from small_binding_v3 import validate\nfrom workspace_binding_v4 import verify as verify_workspace,tool,child_environment")
s=replace(s,"me=K.GetCurrentProcess();","verify_workspace(root)\n me=K.GetCurrentProcess();")
s=replace(s,"cwd=CODE,stdout=out,stderr=err,creationflags=0x08000000,close_fds=True)","cwd=CODE,stdout=out,stderr=err,creationflags=0x08000000,close_fds=True,env=child_environment(root))")
s=s.replace('& logman query -ets',"& 'C:\\Windows\\System32\\logman.exe' query -ets")
put('external_driver_v4.py',s)
s=(N/'native_bridge.py').read_text();s=replace(s,"self.dll=c.WinDLL(str(CODE/'J6OwnedEntry.dll'))","from workspace_binding_v4 import load_dll\n  self.dll=load_dll()")
(C/'native_bridge.py').write_text(s)
put('runtime_scope_v4.ps1',"""function Set-J6RuntimeScope {
 $p=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'shared-runtime-v4.json') -Raw|ConvertFrom-Json
 foreach($n in @('PATH','PSModulePath','PYTHONPATH','PYTHONHOME','TEMP','TMP')) {
  foreach($v in ([Environment]::GetEnvironmentVariable($n) -split ';')) {
   if($v -match '(?i)JARVIS-STAGE6' -and !$v.StartsWith($PSScriptRoot+'\\',[StringComparison]::OrdinalIgnoreCase) -and $v -cne $PSScriptRoot){throw 'Old workspace environment'}
  }
 }
 $env:PSModulePath=$p.moduleRoots -join ';'
 $env:PYTHONNOUSERSITE='1'
 Import-Module -Name (Join-Path $PSHOME 'Modules\\CimCmdlets\\CimCmdlets.psd1') -ErrorAction Stop
}
""")
s=(N/'timed_monitor.ps1').read_text();s=replace(s,". (Join-Path $PSScriptRoot 'health_publication.ps1')",". (Join-Path $PSScriptRoot 'runtime_scope_v4.ps1');Set-J6RuntimeScope\n. (Join-Path $PSScriptRoot 'health_publication.ps1')")
(C/'timed_monitor.ps1').write_text(s)
s=(N/'small_finalize_v3.py').read_text();s=replace(s,'from small_binding_v3 import frozen','from small_binding_v3 import frozen\nfrom workspace_binding_v4 import verify as verify_workspace,tool\nfrom evidence_format_v4 import inspect as inspect_diagnostics')
s=replace(s,"DETAIL={'etw-ready.json'","TOP |= {'workspace-binding-v4.json','loss-diagnostic-v2.json'}\nDETAIL={'loss-diagnostic-v2.json','etw-ready.json'")
s=s.replace("['logman','query','-ets']","[tool('logman'),'query','-ets']")
s=replace(s,'verify_complete(root)\n frozen();','verify_complete(root)\n verify_workspace(root);diagnostics=inspect_diagnostics(root)\n frozen();')
s=replace(s,"write(root/'v3-input-manifest.json',dict(run=root.name,files=before))","verify_workspace(root);need(inspect_diagnostics(root)==diagnostics,'DIAGNOSTIC_CHANGED')\n write(root/'v3-input-manifest.json',dict(run=root.name,files=before,workspaceBindingSHA256=sha(root/'workspace-binding-v4.json'),diagnostics=diagnostics))")
put('small_finalize_v4.py',s)
s=(R/'failure_preserve_v1.py').read_text().replace("['powershell.exe', '-NoProfile'","[r'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe', '-NoProfile'").replace('& logman query -ets',"& 'C:\\Windows\\System32\\logman.exe' query -ets")
s=s.replace('def preserve(run, policy,','def _preserve(run, policy,',1)
a=s.index('def cli_policy():');b=s.index('\ndef verify_candidate',a)
s=s[:a]+'''def cli_policy(run):
    from workspace_binding_v4 import policy as bound_policy,sha,CODE
    p=bound_policy();return dict(candidate=str(CODE),sourceManifestSHA256=sha(CODE/'small-source-v3.json'),preservationRoot=p['preservationRoot'],artifactPatterns=p['artifactPatterns'])

def preserve(run, policy, output_base, failure, **kwargs):
    from workspace_binding_v4 import verify,policy as expected,sha,CODE
    from evidence_format_v4 import inspect
    run=Path(run);p=expected()
    if policy!=cli_policy(run) or Path(output_base)!=Path(p['preservationRoot']):raise ValueError('PRESERVATION_BINDING')
    verify_candidate(policy)
    issues=[]
    try:verify(run)
    except (ValueError,OSError,KeyError) as exc:issues.append(str(exc))
    diagnostics=inspect(run,False)
    # Invalid/missing diagnostics stay forensic evidence, never gain acceptance.
    failure=dict(failure,bindingErrors=issues,diagnosticAdmission=diagnostics)
    return _preserve(run,policy,output_base,failure,**kwargs)

''' +s[b:]
s=s.replace("args=parser.parse_args(); policy=cli_policy()","args=parser.parse_args(); policy=cli_policy(args.run)")
s=s.replace("'final-census-v3.json',\n)","'final-census-v3.json', 'workspace-binding-v4.json', 'loss-diagnostic-v2.json', 'detail/loss-diagnostic-v2.json',\n)")
s=s.replace("partial = bool(missing or exclusions or changed or not clean)","partial = bool(missing or exclusions or changed or not clean or failure.get('bindingErrors') or failure.get('diagnosticAdmission',{}).get('errors'))")
put('failure_preserve_v4.py',s)
p=json.loads((R/'policy.json').read_text());p['schema']='stage6-preservation-policy-v4';p['candidate']=str(C);p.pop('sourceManifestSHA256');p['preservationRoot']=str(C.parent/'preservation-v4')
p['artifactPatterns']+=['workspace-binding-v4\\.json','loss-diagnostic-v2\\.json','detail/loss-diagnostic-v2\\.json']
put('preservation-policy-v4.json',json.dumps(p,indent=2));(C.parent/'preservation-v4').mkdir()
s=(R/'one_run_v1.py').read_text().replace('failure_preserve_v1','failure_preserve_v4').replace('external_driver_v3','external_driver_v4').replace('small_finalize_v3','small_finalize_v4')
s=replace(s,"failure.verify_candidate(policy)","failure.verify_candidate(policy)\n    from workspace_binding_v4 import verify\n    verify(root)")
s=s.replace('failure.cli_policy()','failure.cli_policy(sys.argv[1])')
put('one_run_v4.py',s)
print(json.dumps(dict(candidate=str(C),staged=True,observersLaunched=False)))
