import json,hashlib
from pathlib import Path
R=Path(__file__).parent;C=Path(json.loads((R/'candidate.json').read_text())['code']);p=C/'durable_sink.hpp'
old=p.read_bytes();s=old.decode();a='fault(13);if(!firstFinal)firstFinal=q();'
assert s.count(a)==1
s=s.replace(a,'if(inject==19){std::unique_lock<std::mutex>l(gate);cv.wait(l,[&]{return failure.load()!=0;});throw std::runtime_error("controlled wait-interruption fixture");}\n    '+a)
with (R/'before-injection-correction.hpp').open('xb') as f:f.write(old)
p.write_text(s,encoding='utf8')
with (R/'injection-correction.json').open('x') as f:json.dump(dict(reason='Fault 19 never reached blocked predicate; existing output records zero backpressure and normal completion. Only injected fault 19 now holds finalization until the existing writer wait injects its sticky failure. No normal-path scheduling change.',before=hashlib.sha256(old).hexdigest(),after=hashlib.sha256(p.read_bytes()).hexdigest()),f,indent=2)
