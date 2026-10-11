from pathlib import Path
p=Path(__file__).parent
s=(p/'real_ollama_validation.py').read_text().replace('docs/real-ollama-test','docs/astra-deep-review').replace("'real_local_ollama':True","'deep_review_fixture':True").replace("'real-ollama-electron-'","'astra-pipe-'")
begin=s.index("        a=start_client('teague')")
end=s.index("        with h.Lock(root,'core.lock'):record",begin)
s=s[:begin]+'''        review={'mode':'DEEP_REVIEW','effort':'medium','operation':uuid.uuid4().hex,'task':'Assess the supplied incident only.',
          'evidence':[{'id':'E1','title':'Synthetic incident','text':'Historical root cause unconfirmed; recorded fail-closed behavior. Obtain original traceback.'}]}
        admitted=control('deep-review',{'review':review})
        until=time.monotonic()+5
        while True:
            result=control('request-status',{'request_id':admitted['request_id']})
            if result['done']:break
            if time.monotonic()>until:raise TimeoutError('TEST deep review')
            time.sleep(.02)
        record('authenticated pipe request completed',sum(e['event']=='assistant.completed' for e in result['events'])==1)
        provenance=control('response-provider',{'response_id':admitted['response_id']})
        record('persisted explicit model and fixture label',provenance['provenance']['actual_final_model']=='gpt-6-astra' and provenance['provenance']['simulated'] is True)
        duplicate=control('deep-review',{'review':review})
        record('pipe duplicate remains non-executing',duplicate['duplicate'] and duplicate['response_id']==admitted['response_id'])
        report.append({'case':'pipe provenance evidence','passed':True,'provenance':provenance,'result':result})
        control('shutdown',{'operation':uuid.uuid4().hex});core.wait(8)
        record('authorized shutdown after review',core.returncode==0)
''' +s[end:]
(p/'astra_pipe_probe.py').write_text(s)
