"""Controlled candidate UI validation using existing TEST bootstrap/client fixtures."""
import hashlib,importlib.util,json,sys,time,traceback,uuid
from pathlib import Path

# Use the candidate's matching frozen deployment policy, not unrelated pending
# native/update policy in the working tree. Verify it before importing code.
evidence_dir=Path(sys.argv[1]).resolve()
candidate_record=json.loads((evidence_dir/'candidate.json').read_text())['package']
candidate=Path(candidate_record['package'])
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(candidate/'manifest.json')==candidate_record['sha256']
for entry in json.loads((candidate/'manifest.json').read_text())['files']:
    assert digest(candidate/entry['path'])==entry['sha256']
sys.path.insert(0,str(candidate/'app'))
from deployment_test import contract,enrollment,package,native
assert all(Path(m.__file__).is_relative_to(candidate/'app') for m in (contract,enrollment,package,native))

spec=importlib.util.spec_from_file_location('blank_ui_fixture',Path(__file__).with_name('fixtures.py'))
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def main():
    out=Path(sys.argv[1]).resolve()
    accepted=json.loads((out/'candidate.json').read_text())
    c=f.InstalledCampaign();c.path=out/('actual-client-'+uuid.uuid4().hex+'.json');c.package=accepted['package']
    try:
        old={'pid':3864,'created':134339923015127134}
        c.check('previous exact TEST Core already shut down',c.r.exclusion.process_identity(3864)!=old)
        root,data=c.namespace();b=c.bindings[root];c.seed_records(root)
        core=c.core_config(data);controller,identity=c.start(root,core)
        c.check('candidate Core pinned to new package',identity['runtime_build']==c.package['sha256'])
        c.check('Python cannot impersonate enrolled Electron',c.denied(lambda:c.attach(core,identity,'teague')))
        clients=[c.start_client(root,core,identity,owner) for owner in ('teague','intelligence')]
        c.same_state(*clients,data)
        for client in clients:
            profile=client['ready']['profile']
            c.check('effective main profile is isolated',Path(profile).is_relative_to(b.install/'client-state') if hasattr(b,'install') else Path(profile).is_relative_to(b.state.parent.parent/'client-state'),
                    owner=client['ready']['client'],profile=profile,identity=client['identity'])
        (out/'active-identities.json').write_text(json.dumps({'release':str(b.release),'root':str(root),'core':identity,'clients':[
            {'owner':a['ready']['client'],'identity':a['identity'],'profile':a['ready']['profile'],'stderr':a['stderr']} for a in clients]},indent=2))
        print('CANDIDATE_VISIBLE',out/'active-identities.json',flush=True)
        print('Use VISUAL_PASS only after inspecting actual pixels; STOP preserves a visual failure.',flush=True)
        if input().strip()!='VISUAL_PASS':
            c.check('actual visible UI accepted',False,reason='Blank or unverified pixels; no additional correction')
        c.check('actual visible UI accepted',True,observer='Codex Windows screenshot inspection; not human acceptance')
        for client in clients:
            c.send(client,'capture');shot=c.receive(client,'capture')
            c.check('existing capture command completed',not shot.get('failed'),owner=client['ready']['client'],capture=shot)
        print('CAPTURES_COMPLETE; inspect saved screenshots; enter REGRESS or STOP.',flush=True)
        if input().strip()!='REGRESS':raise RuntimeError('Stopped before regressions; evidence preserved')
        for client in clients:c.close_client(client)
        c.stop(root,core,identity);c.close(controller)
        # Existing actual Electron lifecycle/media/cancellation/restart coverage,
        # using InstalledCampaign overrides and this same candidate package.
        c.client_checks()
        c.check('existing actual-client lifecycle regression complete',True)
    except BaseException:
        c.records.append({'case':'controlled candidate validation failure','passed':False,'traceback':traceback.format_exc()})
        c.save();print(traceback.format_exc(),flush=True)
    finally:
        c.cleanup()
        print(json.dumps({'evidence':str(c.path),'checks':len(c.records),'failures':sum(not r['passed'] for r in c.records)}),flush=True)
    return int(any(not r['passed'] for r in c.records))

if __name__=='__main__':sys.exit(main())
