import concurrent.futures,hashlib,json,pathlib,threading,unittest,uuid
from evidence_io import create_bytes,create_json,create_report,create_run,write_runtime
R=pathlib.Path(__file__).parent
ROOT=R/'tests';ROOT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Preservation(unittest.TestCase):
    def setUp(self):self.root=create_run(ROOT,uuid.uuid4().hex)
    def reject(self,name,writer):
        p=self.root/name;writer(p,'original');before=p.read_bytes();digest=sha(p);stamp=p.stat().st_mtime_ns
        with self.assertRaises(FileExistsError) as e:writer(p,'replacement')
        self.assertIn(str(p),str(e.exception));self.assertEqual(p.read_bytes(),before);self.assertEqual(sha(p),digest);self.assertEqual(p.stat().st_mtime_ns,stamp)
        return p
    def test_01_first_write(self):
        p=self.root/'new.json';create_json(p,{'value':1});self.assertEqual(json.loads(p.read_text()),{'value':1})
    def test_02_second_write_rejected(self):self.reject('second',lambda p,t:create_bytes(p,t.encode()))
    def test_03_bytes_unchanged(self):self.reject('bytes',lambda p,t:create_bytes(p,t.encode()))
    def test_04_hash_unchanged(self):self.reject('hash',lambda p,t:create_bytes(p,t.encode()))
    def test_05_unique_run(self):self.assertTrue(create_run(self.root,'a'*32).is_dir())
    def test_06_runs_do_not_collide(self):self.assertNotEqual(create_run(self.root,'a'*32),create_run(self.root,'b'*32))
    def test_07_json_not_truncated(self):self.reject('final.json',lambda p,t:create_json(p,{'text':t}))
    def test_08_report_not_overwritten(self):self.reject('REPORT.md',create_report)
    def test_09_incident_exclusive(self):self.reject('overwritten.incident.json',lambda p,t:create_bytes(p,t.encode()))
    def test_10_restoration_source_exclusive(self):self.reject('authoritative-original.json',lambda p,t:create_bytes(p,t.encode()))
    def test_11_archive_receipt_exclusive(self):self.reject('archive-verification.json',lambda p,t:create_json(p,{'status':t}))
    def test_12_runtime_remains_mutable(self):
        r=self.root/'runtime';r.mkdir();p=r/'health.json';write_runtime(p,b'one');write_runtime(p,b'two');self.assertEqual(p.read_bytes(),b'two')
    def test_13_explicit_existing_path(self):self.reject('specific-result.json',create_report)
    def test_14_no_delete_recreate_fallback(self):
        p=self.root/'identity';create_bytes(p,b'accepted');before=p.stat()
        for _ in range(3):
            with self.assertRaises(FileExistsError):create_bytes(p,b'other')
        after=p.stat();self.assertEqual((before.st_ino,before.st_size,before.st_mtime_ns),(after.st_ino,after.st_size,after.st_mtime_ns));self.assertEqual(p.read_bytes(),b'accepted')
    def test_15_concurrent_duplicate(self):
        p=self.root/'concurrent';barrier=threading.Barrier(16)
        def worker(i):
            barrier.wait()
            try:create_bytes(p,str(i).encode());return i
            except FileExistsError:return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:out=list(pool.map(worker,range(16)))
        winners=[x for x in out if x is not None];self.assertEqual(len(winners),1);self.assertEqual(p.read_bytes(),str(winners[0]).encode())
    def test_16_mutable_rejects_final(self):
        with self.assertRaises(ValueError):write_runtime(self.root/'final.json',b'x')
    def test_17_run_reuse_rejected(self):
        create_run(self.root,'a'*32)
        with self.assertRaises(FileExistsError):create_run(self.root,'a'*32)
    def test_18_run_traversal_rejected(self):
        with self.assertRaises(ValueError):create_run(self.root,'../old')
if __name__=='__main__':
    import io
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Preservation))
    create_json(R/'focused-tests.json',dict(executed=result.testsRun,passed=result.testsRun-len(result.failures)-len(result.errors),failed=len(result.failures),errored=len(result.errors),skipped=len(result.skipped),output=stream.getvalue(),scope='Sacrificial filesystem writes only; no observers, process workloads or protected files'))
    print(stream.getvalue());raise SystemExit(0 if result.wasSuccessful() else 1)
