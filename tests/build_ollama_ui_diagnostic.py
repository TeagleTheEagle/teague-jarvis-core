from pathlib import Path
p=Path(__file__).parent
s=(p/'real_ollama_validation.py').read_text().replace('docs/real-ollama-test','docs/ollama-acceptance-diagnosis').replace("'real_local_ollama':True","'text_provider_scenario':'temporary'").replace("'real-ollama-electron-'","'ui-diagnostic-'")
s=s.replace("entry=repo/('desktop' if client_id=='teague' else 'intelligence')/'main.cjs'","entry=repo/'tests/ollama_ui_diagnostic.cjs'")
begin=s.index("        a=start_client('teague')");end=s.index("        with h.Lock(root,'core.lock'):record",begin)
s=s[:begin]+'''        a=start_client('teague')
        send(a,'text-fallback',text='What is 2 plus 2? Answer only with the number.',operation=uuid.uuid4().hex)
        result=receive(a,'text-fallback',timeout=30)
        report.append({'case':'offline replay transport result','passed':True,'result':result})
        send(a,'capture');screenshots.append(receive(a,'capture'))
        send(a,'diagnose-render');diagnosis=receive(a,'diagnose-render')
        report.append({'case':'DOM observation only','passed':True,'observation':diagnosis})
        send(a,'capture');screenshots.append(receive(a,'capture'))
        send(a,'close');a['process'].wait(10)
        control('shutdown',{'operation':uuid.uuid4().hex});core.wait(8)
        record('authorized TEST shutdown',core.returncode==0)
''' +s[end:]
(p/'ollama_ui_probe.py').write_text(s)
