import pathlib,json,shutil,subprocess,uuid
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
p=R/'terminal_receipt_v3.hpp';s=p.read_text()
a="if(type=='i'||type=='b'||type=='n')";assert a in s;s=s.replace(a,"if(type=='i'||type=='d'||type=='b'||type=='n')")
a="v.type='i';if(c=='-')v.text+=take();while(p<s.size()&&std::isdigit(static_cast<unsigned char>(s[p])))v.text+=take();if(v.text.empty()||v.text==\"-\"||(v.text.size()>1&&v.text[0]=='0'))throw std::runtime_error(\"integer\");return v;"
b='''v.type='i';if(c=='-')v.text+=take();size_t begin=p;while(p<s.size()&&std::isdigit(static_cast<unsigned char>(s[p])))v.text+=take();if(p==begin||(p-begin>1&&s[begin]=='0'))throw std::runtime_error("integer");if(p<s.size()&&s[p]=='.'){v.type='d';v.text+=take();size_t part=p;while(p<s.size()&&std::isdigit(static_cast<unsigned char>(s[p])))v.text+=take();if(part==p)throw std::runtime_error("fraction");}if(p<s.size()&&(s[p]=='e'||s[p]=='E')){v.type='d';v.text+=take();if(p<s.size()&&(s[p]=='+'||s[p]=='-'))v.text+=take();size_t part=p;while(p<s.size()&&std::isdigit(static_cast<unsigned char>(s[p])))v.text+=take();if(part==p)throw std::runtime_error("exponent");}return v;'''
assert a in s;s=s.replace(a,b)
a='static_cast<unsigned long long>(r.retained)<w.at("localCloseQpc").number()';assert a in s;s=s.replace(a,a+'&&static_cast<unsigned long long>(r.imageBegin)<w.at("localCloseQpc").number()')
# Keep the already-approved error-87 class narrow, with full image and parent evidence.
a='else Require(r.openError==87&&r.stop<r.attemptBegin,"unqualified missing tail handle");'
b='''else {
    auto img=lower(U(r.image));wchar_t device[32768];if(QueryDosDeviceW(L"C:",device,32768)){auto prefix=lower(U(device));if(img.rfind(prefix+"\\\\",0)==0)img="c:"+img.substr(prefix.size());}
    Require(r.openError==87&&r.stop<r.attemptBegin&&r.sequence&&r.created&&img=="c:\\\\windows\\\\system32\\\\conhost.exe"&&ParentKnown(r.parent,r.created,r.parentSequence),"unqualified missing tail handle");
   }'''
assert a in s;s=s.replace(a,b);p.write_text(s);shutil.copyfile(p,C/p.name)
for n in ('coordination_v3.py','evidence_support_v3.py','terminal_control_v3.ps1','test_coordination_v3.py'):shutil.copyfile(R/n,C/n)
result=subprocess.run(['cmd','/d','/c',str(R/'build_native_focused.cmd')],capture_output=True,text=True,timeout=60)
run=C/('offline-native-'+uuid.uuid4().hex);run.mkdir();command=[str(C/'J6ReceiptFixtureV3.exe'),str(run)]
check=subprocess.run(command,capture_output=True,text=True,timeout=10) if result.returncode==0 else None
with (R/'native-real-format-after-fix.json').open('x') as f:json.dump(dict(buildReturncode=result.returncode,buildStdout=result.stdout,buildStderr=result.stderr,command=command,returncode=check.returncode if check else None,stdout=check.stdout if check else None,stderr=check.stderr if check else None),f,indent=2)
print(result.stdout,result.stderr);print(check.stdout if check else '',check.stderr if check else '')
assert result.returncode==0 and check.returncode==0
