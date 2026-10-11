from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'candidate'
def edit(path, old, new):
    file = ROOT / path
    text = file.read_text(encoding='utf-8')
    if text.count(old) != 1: raise RuntimeError(f'{path}: expected one anchor: {old[:70]}')
    file.write_text(text.replace(old, new), encoding='utf-8')

edit('actions.py', 'TOOLS = [', '''from assistant_capabilities import CONTROL_ACTIONS, STATES
TOOLS = [
    schema('assistant_control', 'Operate or check a requested interface control. Use only for an explicit user command. Wait for the requesting interface acknowledgement. Showing a hologram never enables mic or sharing. Screen analysis receives sampled frames, not every video frame. Muted microphones cannot hear an unmute command.', {'action':{'type':'string','enum':list(CONTROL_ACTIONS)}}, ['action']),
    schema('inspection_reports', 'Retrieve archived inspection evidence. Latest/read includes the original report and coverage. Compare compares two archived inspections; missing findings do not prove fixes. No archived report means unavailable, not completed.', {'action':{'type':'string','enum':['list','latest','read','compare']},'inspection_id':STR}, ['action']),
    schema('inspection_findings', 'Read the improvement tracker with evidence, change links and remaining work. Applied but unverified is not verified.', {'status':{'type':'string','enum':['all',*STATES]}}, ['status']),
    schema('inspection_link_change', 'Link a real development proposal to an existing finding, only when requested. Status is read from actual development history. This cannot approve or verify the change.', {'finding_id':STR,'proposal_id':STR}, ['finding_id','proposal_id']),
    schema('manage_timer', 'List active timers; cancel or adjust one exact ID returned by list. Ask which timer when ambiguous. Seconds are measured from now. Confirm only backend success.', {'action':{'type':'string','enum':['list','cancel','adjust']},'timer_id':STR,'seconds':{'type':'number','minimum':1,'maximum':31536000}}, ['action']),
    schema('manage_saved_memory', 'Update or delete a specific saved fact only on explicit request. First list memories; use its exact ID. Ask which fact when ambiguous. Cannot save credentials.', {'action':{'type':'string','enum':['update','delete']},'item_id':STR,'body':STR}, ['action','item_id']),
    schema('response_timings', 'Read measured metadata from the last 20 completed model requests in this process. No transcript or audio stored. Missing stages mean unmeasured. Distinguish provider first token from UI delivery.', {}),''')

edit('server.py', 'import development\n', 'import development\nimport assistant_capabilities as companion_tools\n')
edit('server.py', '        self.approvals = {}', '''        self.approvals = {}
        self.controls = companion_tools.Controls()
        self.inspection_archive = companion_tools.Archive(self.store)
        self.timings = []''')
edit('server.py', "            if name == 'inspect_interface':", '''            if name == 'assistant_control':
                result = self.controls.request(args['action'], run)
            elif name == 'inspection_reports':
                operation = args['action']
                result = self.inspection_archive.list() if operation == 'list' else self.inspection_archive.compare() if operation == 'compare' else self.inspection_archive.read('latest' if operation == 'latest' else args.get('inspection_id', ''))
            elif name == 'inspection_findings':
                result = self.inspection_archive.findings(args['status'])
            elif name == 'inspection_link_change':
                history = development.history(ROOT)['changes']
                proposal = next((r for r in history if r['proposal'] == args['proposal_id']), None)
                if not proposal: raise ValueError('Development proposal not found.')
                status = 'applied but unverified' if proposal['status'] == 'applied' else 'awaiting approval' if proposal['status'] == 'staged' else 'proposed'
                result = self.inspection_archive.track(args['finding_id'], status, {'proposal': proposal['proposal'], 'path': proposal['path'], 'validation': proposal['validation'], 'rollback_reference': proposal['proposal'], 'basis': 'development history; runtime verification not inferred'})
            elif name == 'manage_timer':
                result = companion_tools.manage_timer(self.store, **args)
            elif name == 'manage_saved_memory':
                if run and not re.search(r'\\b(update|correct|change|delete|remove|forget)\\b', run.user_text, re.I):
                    raise ValueError('An explicit saved-memory change request is required.')
                result = companion_tools.manage_memory(self.store, **args)
            elif name == 'response_timings':
                with self.lock: result = {'samples': list(self.timings), 'scope': 'This server process; milliseconds. No cloud benchmark assumed.'}
            elif name == 'inspect_interface':''')
edit('server.py', "            if path == '/api/interface-inspection':", '''            if path == '/api/control-result':
                if set(body) != {'id','run_id','result'}: raise ValueError('Invalid acknowledgement.')
                result = self.app.controls.acknowledge(body['id'], body['run_id'], body['result'])
            elif path == '/api/inspection-finding':
                if set(body) != {'finding','status','note'} or body['status'] not in ('open','verified','deferred','cancelled') or not isinstance(body['note'],str) or not 5 <= len(body['note'].strip()) <= 1000:
                    raise ValueError('Provide a specific observation or decision (5–1000 characters).')
                evidence = {'basis':'user confirmation in interface','note':body['note'],'validation_id':uuid.uuid4().hex,'test_result':'passed' if body['status']=='verified' else 'not asserted'}
                result = self.app.inspection_archive.track(body['finding'],body['status'],evidence)
            elif path == '/api/interface-inspection':''')
edit('server.py', "result=inspection_jobs.start(request,runner,consolidate if transmit and caps.get('vision') else None)", "result=inspection_jobs.start(request,runner,consolidate if transmit and caps.get('vision') else None,on_finish=self.app.inspection_archive.save)")
edit('server.py', 'result=runner(request,threading.Event())', '''result=runner(request,threading.Event())
                    status = 'analysed' if result.get('stages',{}).get('analysis_completed')=='completed' else 'captured' if result.get('stages',{}).get('screenshot_captured')=='completed' else 'failed'
                    result['status']=status
                    job={'id':uuid.uuid4().hex,'status':'completed' if status=='analysed' and not result.get('coverage_limited') else 'partial','request':request,'panels':[request['panel']],'results':[result],'review':result.get('analysis',''),'finished_at':companion_tools.stamp()['at']}
                    try: result['archive']=self.app.inspection_archive.save(job)
                    except Exception: result['archive']={'status':'failed','error':'Report archive failed. Temporary results remain available.'}''')
edit('server.py', 'return inspection_runtime.run(ROOT,database,origin,panel_request,transmit,analyzer,caps.get(\'vision_provider\',\'configured vision provider\'))', '''result=inspection_runtime.run(ROOT,database,origin,panel_request,transmit,analyzer,caps.get('vision_provider','configured vision provider'))
                    if result.get('assessment_mode')=='visual_analysis':
                        try:
                            parsed=json.loads(result['analysis'].strip().removeprefix('```json').removesuffix('```').strip())
                            if not isinstance(parsed.get('review'),str) or not isinstance(parsed.get('findings'),list): raise ValueError()
                            result['analysis']=parsed['review'];result['findings']=parsed['findings'][:60]
                        except (ValueError,TypeError,AttributeError):
                            result.setdefault('limitations',[]).append('Structured findings unavailable; review preserved, tracker not populated from this panel.')
                    return result''')
edit('server.py', "'You are a read-only interface reviewer. You cannot take actions or execute tools.'", "'You are a read-only interface reviewer. You cannot take actions or execute tools. For panel inspection return a JSON object with review (Markdown string) and findings (array of objects: description, priority high/medium/low, recommended_action). Only include observed issues; no actions or verification claims. For cross-panel synthesis return plain Markdown.'")

edit('inspection_jobs.py', 'def start(self, request, runner, summarizer=None, budget=900):', 'def start(self, request, runner, summarizer=None, budget=900, on_finish=None):')
edit('inspection_jobs.py', "job = dict(id=key, status='running', requested_at=stamp(), finished_at=None,", "job = dict(id=key, request=request, status='running', requested_at=stamp(), finished_at=None,")
edit('inspection_jobs.py', 'args=(key, request, runner, summarizer, budget)', 'args=(key, request, runner, summarizer, budget, on_finish)')
edit('inspection_jobs.py', 'def _work(self, key, request, runner, summarizer, budget):', 'def _work(self, key, request, runner, summarizer, budget, on_finish=None):')
edit('inspection_jobs.py', "            cleanup=threading.Timer(301,self._expire,args=(key,))", '''            if on_finish:
                try: archived=on_finish(self.get(key))
                except Exception: archived={'status':'failed','error':'Archiving failed; temporary report retained. Check the improvement project and local storage.'}
                with self.lock: job['archive']=archived
            cleanup=threading.Timer(301,self._expire,args=(key,))''')

# Provider timing events carry metadata only. Buffering stays unchanged until
# live timings justify a retry-safe streaming change.
edit('server.py', '        self.user_text = \'\'', "        self.user_text = ''\n        self.measurements = []\n        self.monotonic_created = time.perf_counter()")
edit('server.py', '                        buffered_events = []\n                        response = providers.chat(messages, available_tools, lambda event, payload: buffered_events.append((event, payload)), run.cancel, vision)', '''                        buffered_events = []
                        provider_started = time.perf_counter()
                        first_delta = None
                        def collect(event, payload):
                            nonlocal first_delta
                            if event=='assistant.delta' and first_delta is None:
                                first_delta=time.perf_counter()
                                run.emit('response.timing', {'stage':'provider first token','ms':round((first_delta-provider_started)*1000)})
                            buffered_events.append((event,payload))
                        response = providers.chat(messages, available_tools, collect, run.cancel, vision)
                        measured={'provider_ms':round((time.perf_counter()-provider_started)*1000),'first_token_ms':None if first_delta is None else round((first_delta-provider_started)*1000),'buffered':True}
                        run.measurements.append(measured)
                        run.emit('response.timing',{'stage':'provider completion','ms':measured['provider_ms']})''')
edit('server.py', '                        time.sleep(1)\n                        response = providers.chat', "                        run.measurements.append({'retry':True,'reason':'stream interruption'})\n                        time.sleep(1)\n                        response = providers.chat")
edit('server.py', "        self.store.audit(name, 'started')", "        tool_started = time.perf_counter()\n        self.store.audit(name, 'started')")
edit('server.py', "                run.emit('tool.completed', {'name': name, 'result': result})", "                run.emit('response.timing', {'stage':'tool '+name,'ms':round((time.perf_counter()-tool_started)*1000)})\n                run.emit('tool.completed', {'name': name, 'result': result})")
edit('server.py', '        finally:\n            with run.condition:\n                run.done = True', '''        finally:
            with self.lock:
                self.timings.append({'finished_at':companion_tools.stamp()['at'],'elapsed_ms':round((time.perf_counter()-run.monotonic_created)*1000),'provider_calls':run.measurements,'cancelled':run.cancel.is_set()})
                self.timings=self.timings[-20:]
            with run.condition:
                run.done = True''')

edit('desktop/preload.cjs', "  showCompanion:()=>ipcRenderer.invoke('jarvis:companion-show'),", "  showCompanion:()=>ipcRenderer.invoke('jarvis:companion-show'),\n  hideCompanion:()=>ipcRenderer.invoke('jarvis:companion-hide'),\n  companionStatus:()=>ipcRenderer.invoke('jarvis:companion-status'),")
edit('desktop/main.cjs', " ipcMain.handle('jarvis:companion-show',event=>{captureSender(event);return showCompanion();});", ''' ipcMain.handle('jarvis:companion-show',async event=>{captureSender(event);await showCompanion();for(let i=0;i<100;i++){if(companion&&!companion.isDestroyed()&&companion.isVisible())return {shown:true};await new Promise(r=>setTimeout(r,50));}return {shown:false,error:'Companion did not become visible.'};});
 ipcMain.handle('jarvis:companion-hide',event=>{captureSender(event);if(companion&&!companion.isDestroyed())companion.hide();return {visible:!!companion&&!companion.isDestroyed()&&companion.isVisible()};});
 ipcMain.handle('jarvis:companion-status',event=>{captureSender(event);return {visible:!!companion&&!companion.isDestroyed()&&companion.isVisible()};});''')

edit('static/app.js', '(?:float|show|open)(?: the| your| my)? (?:hologram|companion|floating jarvis)', '(?:activate|float|show|open)(?: the| your| my)? (?:hologram|companion|floating jarvis)')
edit('static/app.js', "      if(event.event==='assistant.delta'){if(!firstResponse)", "      if(event.event==='control.requested'){void performAssistantControl(event.data.action).then(result=>api('/api/control-result',{id:event.data.id,run_id:state.run,result})).catch(()=>toast('Control acknowledgement failed; no success confirmed.',true));}\n      if(event.event==='response.timing'){voiceDiagnostic(event.data.stage,event.data.ms+' ms');}\n      if(event.event==='assistant.delta'){if(!firstResponse)")
edit('static/app.js', "async function send(text,screenAttachment=null,options={}){ if(window.JARVIS_INSPECTION)return;", "async function send(text,screenAttachment=null,options={}){ if(window.JARVIS_INSPECTION)return;\n  const localControl=!screenAttachment&&!state.attachment&&assistantControlIntent(text);\n  if(localControl){const result=await performAssistantControl(localControl);message('user',text);message('assistant',controlSummary(localControl,result));return;}")
edit('static/app.js', "      if(JarvisVoice.isEndPhrase(text))", "      if(assistantControlIntent(text)){state.transcribing=false;void send(text);return;}\n      if(JarvisVoice.isEndPhrase(text))")
edit('static/app.js', "if(state.busy||state.transcribing)return;const text=$('#messageInput').value;", "if((state.busy||state.transcribing)&&!assistantControlIntent($('#messageInput').value))return;const text=$('#messageInput').value;")
edit('static/inspection-client.js', "heading.textContent='Whole inspection review · '+job.review_status;", "heading.textContent='Whole inspection review · '+job.review_status;\n          const archived=document.createElement('p');archived.textContent=job.archive?.status==='archived'?'Archived in Project Jarvis · '+job.archive.inspection_id:job.archive?.error||'Archive status not yet confirmed.';review.append(archived);")

print('Candidate wiring complete; live source unchanged.')
