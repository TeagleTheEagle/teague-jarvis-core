import pathlib,json,hashlib,ast,re
R=pathlib.Path(__file__).parent
allruns=[]
for name in ('dry1','dry2'):
 d=R/name;result=json.loads((d/'result.json').read_text());assert result['status']=='PASS'
 assert not (d/'resources-error.txt').exists()
 resources=[json.loads(s) for s in (d/'resources.jsonl').read_text(encoding='utf-8-sig').splitlines()]
 counters=[c for row in resources for c in row['counters']]
 def vals(s):return [c['CookedValue'] for c in counters if s in c['Path'].lower()]
 result['resource_samples']=len(resources);result['peak_total_cpu_percent']=max(vals('processor(_total)'))
 result['peak_c_disk_active_percent']=max(100-v for v in vals('physicaldisk(1 c:)\\% idle time'))
 result['peak_c_disk_queue']=max(vals('physicaldisk(1 c:)\\current disk queue length'))
 result['minimum_available_memory_mb']=min(vals('available mbytes'))
 assert hashlib.sha256((d/'sacrificial-manifest.json').read_bytes()).hexdigest()==(d/'sacrificial-manifest.sha256').read_text().strip()
 allruns.append(result)
names=['VirtualBox.exe','VirtualBoxVM.exe','VBoxHeadless.exe','VBoxManage.exe','VBoxSVC.exe','VBoxSDS.exe']
coverage={n:bool(re.match(r'^(VBox|VirtualBox)',n)) and bool(re.match(r'^(VBox|VirtualBox)',n[:13])) for n in names};assert all(coverage.values())
source=[]
for p in sorted(R.glob('*.py')):ast.parse(p.read_text());source.append(p)
source+=sorted(R.glob('*.ps1'))
summary={'dry_runs':allruns,'combined_starts':sum(r['captured_starts'] for r in allruns),'combined_stops':sum(r['captured_stops'] for r in allruns),'static_name_prefix_coverage_only':coverage,'actual_VirtualBox_processes_launched':False,'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source},'historical_13_7_second_cause':'UNCONFIRMED','historical_stage1_cause':'UNCONFIRMED'}
(R/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True));print(json.dumps(summary,indent=2))
