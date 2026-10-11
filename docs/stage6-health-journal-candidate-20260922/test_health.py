import copy,ctypes,hashlib,json,os,pathlib,queue,subprocess,sys,threading,time,unittest,uuid
from unittest.mock import patch
R=pathlib.Path(__file__).resolve().parent
C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
sys.path.insert(0,str(C))
from health_reader import HealthReader
from journal import frequency,ticks,encode,Unhealthy
from workspace import new_run,activate_temp
ROOT=new_run('health-tests-'+uuid.uuid4().hex);activate_temp(ROOT)
class Watch:
    def __init__(self,identity):self.closed=False;self.dead=False
    def check(self):
        if self.dead:raise Unhealthy('dead')
    def close(self):self.closed=True
class Protocol(unittest.TestCase):
    def setUp(self):
        self.r=new_run('health-unit-'+uuid.uuid4().hex);self.now=frequency()*100;self.p=self.r/'app-health.jsonl';self.p.touch();self.h=None
        self.ready=dict(pid=123,created='456',frequency=frequency());self.seq=0
    def tearDown(self):
        if self.h:self.h.close();self.assertTrue(self.h.watch.closed)
    def row(self,**kw):
        self.seq+=1;v=dict(self.ready,run=self.r.name,seq=self.seq,pump=self.seq,ticks=self.now,utc='synthetic',state='ACTIVE',violations=0);v.update(kw);return v
    def put(self,v):
        with self.p.open('ab',buffering=0) as f:f.write(encode(v))
    def reader(self):
        self.h=HealthReader(self.r,self.ready,clock=lambda:self.now,watch_factory=Watch);return self.h
    def rejection(self):
        with self.assertRaises((Unhealthy,ValueError,OSError)):self.h.poll()
        with self.assertRaises(Unhealthy):self.h.poll()
    def test_01_sequential(self):
        self.put(self.row());h=self.reader();self.assertEqual(h.poll()['sequence'],1);self.put(self.row());self.assertEqual(h.poll()['sequence'],2)
    def test_02_partial_does_not_renew(self):
        self.put(self.row());h=self.reader();h.poll();self.now+=frequency()*9;b=encode(self.row());self.p.open('ab').write(b[:20]);self.assertEqual(h.poll()['sequence'],1);self.now+=frequency();self.rejection()
    def test_03_partial_completion(self):
        self.put(self.row());h=self.reader();h.poll();b=encode(self.row())
        with self.p.open('ab',buffering=0) as f:f.write(b[:20]);self.assertEqual(h.poll()['sequence'],1);f.write(b[20:])
        self.assertEqual(h.poll()['sequence'],2)
    def test_04_empty(self):self.reader();self.rejection()
    def test_05_partial_initial(self):self.p.write_bytes(b'{');self.reader();self.rejection()
    def test_06_malformed_complete(self):self.put(self.row());self.p.open('ab').write(b'broken\n');self.reader();self.rejection()
    def test_07_duplicate(self):v=self.row();self.put(v);self.put(v);self.reader();self.rejection()
    def test_08_skip(self):self.put(self.row(seq=2));self.reader();self.rejection()
    def test_09_wrong_identity(self):
        for field,value in [('run','OTHER'),('pid',124),('created','457'),('frequency',frequency()+1)]:
            with self.subTest(field=field):
                self.seq=0;self.p.write_bytes(b'');self.put(self.row(**{field:value}));self.reader();self.rejection();self.h.close()
    def test_10_inactive(self):self.put(self.row(state='FAILED'));self.reader();self.rejection()
    def test_11_violation(self):self.put(self.row(violations=1));self.reader();self.rejection()
    def test_12_future(self):self.put(self.row(ticks=self.now+1));self.reader();self.rejection()
    def test_13_exact_ten(self):self.put(self.row());self.reader();self.now+=10*frequency();self.rejection()
    def test_14_below_ten(self):self.put(self.row());h=self.reader();self.now+=10*frequency()-1;self.assertLess(h.poll()['age'],10)
    def test_15_above_ten(self):self.put(self.row());self.reader();self.now+=10*frequency()+1;self.rejection()
    def test_16_dead_publisher(self):self.put(self.row());h=self.reader();h.watch.dead=True;self.rejection()
    def test_17_truncation(self):self.put(self.row());h=self.reader();h.poll();self.p.write_bytes(b'');self.rejection()
    def test_18_path_replacement(self):
        self.put(self.row());h=self.reader();h.poll();st=self.p.stat()
        class S:st_dev=st.st_dev;st_ino=st.st_ino+1;st_size=st.st_size
        with patch.object(pathlib.Path,'stat',return_value=S()):self.rejection()
    def test_19_denied(self):
        self.put(self.row());self.reader()
        with patch.object(pathlib.Path,'stat',side_effect=PermissionError('injected')):self.rejection()
    def closure(self):
        (self.r/'release-handles').write_text(json.dumps(dict(observerExited=True)))
        (self.r/'app-result.json').write_text(json.dumps(dict(success=True,durableFinalization=True)))
    def test_20_finalize_complete(self):self.put(self.row());h=self.reader();h.poll();self.closure();self.assertTrue(h.finalize()['complete'])
    def test_21_finalize_partial(self):
        self.put(self.row());h=self.reader();h.poll();self.closure();self.p.open('ab').write(b'{')
        with self.assertRaises(Unhealthy):h.finalize()
    def test_22_finalize_unproven(self):
        self.put(self.row());h=self.reader();h.poll()
        with self.assertRaises(OSError):h.finalize()
    def test_23_invalid_frequency(self):
        for f in (0,-1,True,frequency()+1):
            with self.assertRaises(Unhealthy):HealthReader(self.r,dict(self.ready,frequency=f),watch_factory=Watch)
    def test_24_latched_boundary(self):
        self.put(self.row());h=self.reader();self.now+=10*frequency();self.rejection();self.put(self.row());self.rejection()
    def test_25_closed_reader(self):self.put(self.row());h=self.reader();h.close();self.rejection()

PS=r'''param([string]$Root,[string]$Code,[string]$Mode)
$ErrorActionPreference='Stop'
. (Join-Path $Code 'health_publication.ps1')
function Signal($s){[Console]::Out.WriteLine($s);[Console]::Out.Flush()}
function Gate {if([Console]::In.ReadLine() -ne 'GO'){throw 'test gate rejected'}}
if($Mode -eq 'old'){
 $p=Join-Path $Root 'old.json';[IO.File]::WriteAllText($p,'{"healthy":true}')
 $f=[IO.FileStream]::new($p,[IO.FileMode]::Create,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{Signal 'TRUNCATED';Gate;$b=[Text.Encoding]::UTF8.GetBytes('{"healthy":true}');$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}
 Signal 'DONE';exit 0
}
$me=Get-Process -Id $PID;$frequency=[Diagnostics.Stopwatch]::Frequency
$i=@{run=(Split-Path $Root -Leaf);pid=$PID;created=$me.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();frequency=$frequency}
$pub=New-J6HealthPublisher $Root $i
try {
 try{Publish-J6Ready $Root $pub $i;throw 'unexpected ready'}catch{if($_.Exception.Message -ne 'No completed initial health publication'){throw}}
 Signal 'EMPTY';Gate
 Write-J6HealthRecord $pub ([Diagnostics.Stopwatch]::GetTimestamp())
 Publish-J6Ready $Root $pub $i
 Signal 'READY';Gate
 $row=@{run=$i.run;pid=$PID;created=$i.created;frequency=$frequency;seq=2;pump=2;ticks=[Diagnostics.Stopwatch]::GetTimestamp();utc=[DateTime]::UtcNow.ToString('o');state='ACTIVE';violations=0}
 $b=[Text.Encoding]::UTF8.GetBytes((($row|ConvertTo-Json -Compress)+"`n"));$cut=[int]($b.Length/2)
 $pub.Stream.Write($b,0,$cut);$pub.Stream.Flush($true);Signal 'PARTIAL';Gate
 if($Mode -eq 'interrupted'){throw 'controlled interrupted publication'}
 $pub.Stream.Write($b,$cut,$b.Length-$cut);$pub.Stream.Flush($true);$pub.Sequence=2;Signal 'COMPLETE';Gate
 for($n=0;$n -lt 25;$n++){Write-J6HealthRecord $pub ([Diagnostics.Stopwatch]::GetTimestamp());Signal 'RECORD';Gate}
 Close-J6HealthPublisher $pub;Signal 'CLOSED';Gate
}finally{if(!$pub.Closed){$pub.Stream.Dispose();$pub.Closed=$true}}
'''
script=ROOT/'writer.ps1';script.write_text(PS,encoding='utf8')
PWSH=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
processes=[]
class Integration(unittest.TestCase):
    def start(self,mode):
        root=new_run('health-ps-'+uuid.uuid4().hex)
        p=subprocess.Popen([PWSH,'-NoProfile','-File',str(script),'-Root',str(root),'-Code',str(C),'-Mode',mode],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=0x08000000,cwd=C)
        q=queue.Queue();thread=threading.Thread(target=lambda:[q.put(line.strip()) for line in p.stdout],daemon=True);thread.start()
        self.addCleanup(self.cleanup,p,thread,root)
        return root,p,q
    def cleanup(self,p,thread,root):
        if p.poll() is None:
            p.stdin.close()
            try:p.wait(10)
            except subprocess.TimeoutExpired:raise AssertionError('TEST writer cleanup unproven; stop')
        thread.join(2);self.assertFalse(thread.is_alive());err=p.stderr.read()
        processes.append(dict(pid=p.pid,exit=p.returncode,stderr=err,root=str(root),retainedPopenExitConfirmed=p.returncode is not None))
        p.stdout.close();p.stderr.close()
        if not p.stdin.closed:p.stdin.close()
    def expect(self,q,v):self.assertEqual(q.get(timeout=10),v)
    def go(self,p):p.stdin.write('GO\n');p.stdin.flush()
    def test_26_old_race_reproduced(self):
        root,p,q=self.start('old');self.expect(q,'TRUNCATED')
        with self.assertRaises(json.JSONDecodeError):json.loads((root/'old.json').read_text())
        self.go(p);self.expect(q,'DONE');self.assertEqual(p.wait(10),0)
    def exercise(self,mode):
        root,p,q=self.start(mode);self.expect(q,'EMPTY');self.assertFalse((root/'app-ready.json').exists());self.go(p);self.expect(q,'READY')
        h=HealthReader(root,json.loads((root/'app-ready.json').read_text()));self.addCleanup(h.close)
        self.assertEqual(h.poll()['sequence'],1);self.go(p);self.expect(q,'PARTIAL');self.assertEqual(h.poll()['sequence'],1);self.assertGreater(h.reader.pending.__len__(),0);self.go(p)
        if mode=='interrupted':
            self.assertNotEqual(p.wait(10),0)
            with self.assertRaises(Unhealthy):h.poll()
            return
        self.expect(q,'COMPLETE');self.assertEqual(h.poll()['sequence'],2);self.go(p)
        for seq in range(3,28):self.expect(q,'RECORD');self.assertEqual(h.poll()['sequence'],seq);self.go(p)
        self.expect(q,'CLOSED');self.assertEqual(h.poll()['sequence'],27)
        self.go(p);self.assertEqual(p.wait(10),0)
        (root/'release-handles').write_text('{"observerExited":true}');(root/'app-result.json').write_text('{"success":true,"durableFinalization":true}')
        self.assertEqual(h.finalize()['sequence'],27)
    def test_27_real_writer_reader(self):self.exercise('normal')
    def test_28_interrupted_writer(self):self.exercise('interrupted')

with (ROOT/'tests.txt').open('x') as f:
    result=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(['Protocol','Integration'],sys.modules[__name__]))
out=dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),root=str(ROOT),processes=processes)
(ROOT/'result.json').write_text(json.dumps(out,indent=2));(R/'focused-result.json').write_text(json.dumps(out,indent=2));print(json.dumps(out));sys.exit(not result.wasSuccessful())
