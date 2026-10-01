"""New test executable with explicit payload size; retains failed v1 unchanged."""
import pathlib,json,shutil,subprocess,hashlib
R=pathlib.Path(__file__).parent;plan=json.loads((R/'plan.json').read_text());old=pathlib.Path(plan['code']);C=old.parent/'representative-code';C.mkdir()
shutil.copy2(old/'trace_sink.hpp',C/'trace_sink.hpp')
s=(old/'stream_bench.cpp').read_text().replace('argc!=8','argc!=9')
s=s.replace('std::string payload=', 'unsigned padding=wcstoul(argv[8],0,10);if(padding>600)return 93;\n std::string payload=').replace("std::string(600,'x')","std::string(padding,'x')")
(C/'stream_bench.cpp').write_text(s)
original=json.loads((R/'build.json').read_text());args=[a.replace(str(old),str(C)) for a in original['args']]
p=subprocess.run(args,cwd=C,capture_output=True,text=True)
(R/'representative-build.json').write_text(json.dumps(dict(code=str(C),args=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,headerSHA256=hashlib.sha256((C/'trace_sink.hpp').read_bytes()).hexdigest()),indent=2))
print('BUILD',p.returncode);raise SystemExit(p.returncode)
