"""Keep old predicates; give existing archive/tracker fixtures explicit new seams."""
import pathlib,json
R=pathlib.Path(__file__).parent;v=json.loads((R/'before.json').read_text());P=pathlib.Path(v['predecessor']);C=pathlib.Path(v['candidate'])
s=(P/'test_binding_v4.py').read_text()
s=s.replace("m.patch('completed_v3.verify_complete',return_value={}),","m.patch('completed_v3.verify_complete',return_value={}),m.patch('helper_handoff_v1.verify_final',return_value={'offlineFixture':True}),")
(C/'test_binding_v4.py').write_text(s)
s=(P/'test_successor_v3.py').read_text()
# Existing tracker close-error/class tests retain their role; fresh full handoff tests live separately.
s=s.replace("t,r=self.build();root=ROOT/uuid.uuid4().hex;root.mkdir();clock=itertools.count(1000)","t,r=self.build();root=ROOT/uuid.uuid4().hex;root.mkdir();(root/'observer-identities.json').write_text(json.dumps({'etw':{'pid':99,'created':'900'}}));clock=itertools.count(1000)")
s=s.replace("patch.object(tracker.K,'WaitForSingleObject',return_value=258)","patch.object(tracker.K,'OpenProcess',return_value=3),patch.object(tracker,'times',return_value=('900',None)),patch('helper_handoff_v1.perform',return_value={'observedQpc':999}),patch.object(tracker.K,'WaitForSingleObject',return_value=258)")
(C/'test_successor_v3.py').write_text(s)
