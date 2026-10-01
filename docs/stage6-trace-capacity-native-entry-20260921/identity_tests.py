import pathlib,json,sys,uuid,shutil
from unittest.mock import patch
R=pathlib.Path(__file__).parent;M=R/'medium-candidate';C=pathlib.Path(json.loads((M/'plan.json').read_text())['code']);sys.path.insert(0,str(C));import integration_verify
O=pathlib.Path(json.loads((R/'batched-candidate/plan.json').read_text())['code'])/'protected-5d26ae153ea2490da7ca1ec16d97c124'
assert integration_verify.inspect(O)['nativeEntries']==5
results=[]
for case in ('missing-native','wrong-creation','wrong-pid','duplicate-native','missing-entry','late-entry','missing-python'):
 root=C/('identity-'+uuid.uuid4().hex);root.mkdir()
 for name in ('etw-result.json','stress-result.json','native-bridge-cleanup.json'):shutil.copy2(O/name,root/name)
 for pattern in ('native-*-*.json','integration-*-*.json'):
  for f in O.glob(pattern):shutil.copy2(f,root/f.name)
 native=next(p for p in root.glob('native-*.json') if p.name!='native-bridge-cleanup.json');data=json.loads(native.read_text())
 if case=='missing-native':native.rename(root/'removed-native.evidence')
 elif case=='duplicate-native':shutil.copy2(native,root/'native-99999-999.json')
 elif case=='missing-python':
  marker=next(root.glob('integration-collector-*.json'));marker.rename(root/'removed-marker.evidence')
 else:
  if case=='wrong-creation':data['created']=str(int(data['created'])+1)
  elif case=='wrong-pid':data['pid']+=100000
  elif case=='missing-entry':data['events']=[x for x in data['events'] if x['event']!='PE_ENTRY_EXECUTED']
  elif case=='late-entry':data['entryQpc']=2**62
  native.write_text(json.dumps(data))
 with patch.object(integration_verify,'verify',return_value={'fixture':'trace verifier separately tested'}):
  try:integration_verify.inspect(root)
  except (AssertionError,StopIteration):results.append(dict(case=case,rejected=True))
  else:raise AssertionError('Identity failure accepted: '+case)
(R/'identity-tests.json').write_text(json.dumps(dict(positiveSmallRecheck=True,negativeChecks=results),indent=2));print('Actual small positive recheck + 7 negative identity/entry tests PASS')
