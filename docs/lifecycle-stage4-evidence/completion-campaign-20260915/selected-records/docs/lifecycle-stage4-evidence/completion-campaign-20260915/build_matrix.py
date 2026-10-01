import pathlib,re,json,csv,hashlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=pathlib.Path(__file__).resolve().parent
text=pathlib.Path('C:/Users/jonny/.codex/attachments/9a816a6e-52a1-4933-97f8-d89a8c461105/pasted-text.txt').read_text(encoding='utf-8')
items=re.findall(r'^(\d+)\. (.+)$',text.split('REQUIRED TEST MATRIX')[1].split('MANUAL ISOLATED')[0],re.M);assert len(items)==47
R='restart-campaign-5a9ac2730cbe4c1da318e710793af901.json';M='client-state-media-a9cbccc28f354831aee61a48f2d2727d.json';E='electron-app-probe-6425a1f8fb814e4b83ed6c48250ec55a.json';N='real-app-probe-300aa76e07d4436ab50e2db959287f16.json'
rows=[]
for n,title in items:
 number=int(n);status='PASS';evidence=N;limit='Actual isolated App; deterministic providers and silent media.'
 if number in (1,2,20,21,22,23,24,25,26,27,32,33,43):evidence=R;limit='Finite real process campaign: 4x8 contenders, 3 coordinator-loss, 3 Core-crash rounds. Startup methods unchanged at final baseline.'
 if number in (5,6,7,8,14,15,16,17,28,29,30,31,34,35,39):evidence=M if number in (28,30,31,34,35) else E;limit='Actual Electron; canonical records through authenticated client bridge; no hardware.'
 if number in (3,4):evidence='completion-campaign-20260915/ownership-175914.log';limit='Provisioning/open-existing guard; no production Store.'
 if number in (40,41,42):evidence='completion-campaign-20260915/bootstrap-180332.log; completion-campaign-20260915/native-180332.log; completion-campaign-20260915/ownership-175914.log';limit='Negative native/bootstrap probes plus ownership boundaries; no client startup authority.'
 if number==37:status='LIMITATION';evidence='completion-campaign-20260915/final-source-hashes.json';limit='Original shadow-only wording superseded only for explicitly approved TEST providers; production routing unchanged.'
 if number==38:evidence='completion-campaign-20260915/repair-175914.log; completion-campaign-20260915/repair-loop-175914.log; completion-campaign-20260915/python-180332.log';limit='Synthetic repair cleanup/accounting; no real repair or universal monetary-metering claim.'
 if number in (44,45,46):
  stage=number-43;evidence=f'completion-campaign-20260915/stage{stage}-175914.log';limit={1:'23 pass / 1 existing skip',2:'35 pass / 1 existing skip',3:'43 pass; unchanged suite'}[stage]
 if number==47:status='LIMITATION';evidence='../CANONICAL-CORE-STAGE-4.md; ../STAGE4-REMAINING-REQUIREMENTS-20260915.md';limit='Assessment complete; historical root cause UNCONFIRMED / FAIL-SAFE / REVIEW REQUIRED. Separate reproduced mechanisms preserved.'
 if number==21:limit='Explicit authenticated transaction reconciles retained stop marker; no deletion. Ordinary startup remains denied.'
 rows.append({'id':f'S4-REQ-{number:02d}','requirement':title,'disposition':status,'evidence':evidence,'limitations':limit})
for ident,requirement,status,evidence,limit in [
 ('APPROVALS','Authenticated TEST approvals','DEFERRED','Owner scope decision','Absent product workflow; excluded, not PASS'),
 ('UPLOADS','Authenticated TEST uploads','DEFERRED','Owner scope decision','Separate authority/persistence review'),
 ('RESPONSE','Shared cancellation/response persistence','PASS','completion-campaign-20260915/response-commit-175914.log; completion-campaign-20260915/independent-sqlite-final.json','306 fresh trials / 4748 assertions; prior 918 retained, not added'),
 ('MEDIA','Client lease watchdog/distinct controls','PASS',M+'; client-state-media-20260915/watchdog-unit-01.log','Modeled mechanics; physical media deferred'),
 ('HUMAN','Human selection and emergency/shutdown controls','OPEN','../STAGE4-HUMAN-LIFECYCLE-CHECK.md','User intends to run; completed operator record not received. Blocks Stage 4 and Stage 5'),
 ('PHYSICAL','Physical microphone/headset/live voice','DEFERRED','Owner decision and ownership/drain design','No hardware authority; not PASS'),
 ('ENV','Restricted-context Electron GPU finding','LIMITATION','electron-gpu-diagnosis-20260915/REVIEW.md','44.2.0; STATUS_DLL_NOT_FOUND-compatible exit; exact DLL/root cause UNCONFIRMED; host context passes')]:
 rows.append({'id':'S4-'+ident,'requirement':requirement,'disposition':status,'evidence':evidence,'limitations':limit})
(OUT/'requirement-to-evidence.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
with (OUT/'requirement-to-evidence.csv').open('w',newline='',encoding='utf-8') as file:
 writer=csv.DictWriter(file,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
files=['stage4_runtime.py','stage4_sessions.py','stage4_lifecycle.py','stage4_response_history.py','stage4_provider_fallback.py','stage4_deep_review.py','stage4_ollama_transport.py','server.py','store.py','tests/lifecycle_stage4/fixtures.py','tests/lifecycle_stage4/test_stage4.py','tests/provider_fallback_integration.py','tests/astra_deep_review_integration.py']
results=[]
for name in files:
 source=(ROOT/name).read_bytes();compile(source,name,'exec');results.append({'file':name,'command':'compile(source_bytes, filename, exec); no execution','passed':True,'sha256':hashlib.sha256(source).hexdigest()})
node=pathlib.Path('C:/Users/jonny/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
for name in ['stage4_client.cjs','desktop/main.cjs','desktop/preload.cjs','intelligence/main.cjs','intelligence/stage4-renderer.js','desktop/test/stage4-client.test.cjs']:
 result=subprocess.run([str(node),'--check',str(ROOT/name)],capture_output=True,text=True)
 results.append({'file':name,'command':[str(node),'--check',name],'passed':result.returncode==0,'exit':result.returncode,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()})
(OUT/'standalone-syntax.json').write_text(json.dumps(results,indent=2));print('requirements',len(rows),'syntax',len(results),'passed',all(x['passed'] for x in results))
