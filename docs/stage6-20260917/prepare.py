"""Stage the accepted application plus only three reviewed deployment differences."""
from pathlib import Path
import difflib,hashlib,json,shutil,subprocess,uuid
R=Path(__file__).resolve().parents[2];D=Path(__file__).parent
base=R/'docs/deployment-completion-20260917/final-blockers/accepted-app'
S=R.parent/('TEST-STAGE6-SOURCE-'+uuid.uuid4().hex);S.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for p in base.rglob('*'):
    if p.is_file():
        t=S/p.relative_to(base);t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,t);rows.append({'path':p.relative_to(base).as_posix(),'sha256':sha(p)})
changes=[]
for name in ('contract.py','native.py','package.py'):
    relative='deployment_test/'+name;old=base/relative;pending=R/relative;target=S/relative
    for label,p in (('accepted',old),('pending',pending)):
        out=D/label/relative;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
    shutil.copyfile(pending,target)
    if name=='native.py':
        text=target.read_text();oldline="            else:need(path.is_relative_to(Path(os.environ['SystemRoot'])),'UNDECLARED_LOADED_NATIVE:'+str(path))"
        assert text.count(oldline)==1
        target.write_text(text.replace(oldline,"            elif not package_name:need(path.is_relative_to(Path(os.environ['SystemRoot'])),'UNDECLARED_LOADED_NATIVE:'+str(path))"))
    out=D/'candidate'/relative;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(target,out)
    (D/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),target.read_text().splitlines(True),fromfile='accepted/'+relative,tofile='candidate/'+relative)))
    changes.append({'path':relative,'accepted':sha(old),'pending':sha(pending),'candidate':sha(target)})
for relative in ('tests/lifecycle_stage4/fixtures.py','tests/lifecycle_stage5/campaign.py','tests/deployment_contract/fixtures.py','tests/deployment_contract/completion.py','tests/deployment_contract/test_contract.py'):
    t=S/relative;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/relative,t)
for name in ('docs/deployment-completion-20260916','docs/lifecycle-stage4-evidence','docs/lifecycle-stage5-evidence','tests/lifecycle_stage1/evidence'):(S/name).mkdir(parents=True,exist_ok=True)
record={'source':str(S),'baseline_commit':'9460dbc44f63c95d1128c1a27f124f87d99b530b','accepted_files':rows,'deployment_changes':changes,'production_changed':False}
(D/'source.json').write_text(json.dumps(record,indent=2));print(json.dumps({'source':str(S),'files':len(rows),'changes':changes}))
