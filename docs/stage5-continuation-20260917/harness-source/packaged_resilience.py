"""Actual TEST client gate, frozen package and explicit packaged Electron identity."""
from pathlib import Path
import importlib.util,json,sys,traceback,types,uuid
R=Path(__file__).resolve().parents[2];D=R/'docs/stage5-continuation-20260917'
APP=Path(json.loads((R/'docs/stage5-accepted-baseline-20260917/baseline.json').read_text())['app'])
sys.argv=[sys.argv[0],str(D)]
spec=importlib.util.spec_from_file_location('validated_packaged_driver',APP/'tests/deployment_contract/blank_ui_validation.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
sys.path.insert(0,str(R/'tests/lifecycle_stage5'))
from continued_campaign import Continued
c=driver.f.InstalledCampaign();c.package=driver.candidate_record
c.electron=driver.candidate/'electron/electron.exe'
c.path=D/('5D-'+uuid.uuid4().hex+'.json');c.timeline=[]
c.start=types.MethodType(Continued.start,c);c.stamp=types.MethodType(Continued.stamp,c)
try:c.client_checks()
except BaseException:
    c.records.append({'case':'actual-client failure','passed':False,'traceback':traceback.format_exc()});c.save();raise
finally:c.cleanup()
print(json.dumps({'evidence':str(c.path),'checks':len(c.records),'failures':sum(not x['passed'] for x in c.records)}))
assert all(x['passed'] for x in c.records)
