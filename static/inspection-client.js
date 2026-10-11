'use strict';
(() => {
  if(window.JARVIS_INSPECTION)return;
  const panels=[...new Set([...document.querySelectorAll('.nav[data-view]')].map(el=>el.dataset.view).filter(name=>document.getElementById(name+'View')))];
  const dialog=document.createElement('dialog');dialog.setAttribute('aria-label','Interface inspection');
  dialog.innerHTML='<h2>Inspect JARVIS</h2><p>Inspect a separate read-only copy. Your current page stays in place. Private saved text is masked; this reviews layout and controls.</p><label>Panel <select id="inspectionPanel"></select></label><label>Coverage <select id="inspectionScope"><option value="viewport">Viewport</option><option value="full_panel">Bounded panel sections</option></select></label><label>Focus <input id="inspectionFocus" maxlength="2000"></label><p id="inspectionRecipient"></p><label><input type="checkbox" id="inspectionTransmit"> Automatically analyse my requested inspections with this provider. Masked captures and my focus question are sent; provider retention policies apply.</label><p>Your inspection request starts analysis automatically. Uncheck for a local-only inspection. Captures expire after five minutes and are not archived. Completed, partial and failed reports are saved locally in Project Jarvis; archive success is shown separately.</p><button id="inspectionStart">INSPECT</button><button id="inspectionStop" disabled>STOP AFTER CURRENT PANEL</button><button id="inspectionClose">CLOSE</button><p id="inspectionStatus" role="status"></p><div id="inspectionResults"></div>';
  document.body.append(dialog);
  const el=id=>dialog.querySelector('#'+id);
  panels.forEach(p=>el('inspectionPanel').add(new Option(p,p)));
  el('inspectionPanel').add(new Option('Whole interface (sequential)','all'));
  let running=false,stop=false,jobId=null;
  window.openInterfaceInspection=(request={})=>{
    if(running){dialog.showModal();return;}
    el('inspectionPanel').value=panels.includes(request.panel)?request.panel:'command';
    if(request.panel==='all')el('inspectionPanel').value='all';
    el('inspectionScope').value=request.scope==='viewport'?'viewport':'full_panel';
    el('inspectionFocus').value=typeof request.focus==='string'?request.focus.slice(0,2000):'';
    el('inspectionTransmit').checked=true;
    el('inspectionRecipient').textContent='Analysis recipient: '+(state.data?.capabilities?.vision_provider||'configured vision provider (availability not verified)');
    if(!dialog.open)dialog.showModal();
  };
  async function cancel(){stop=true;if(jobId)try{await api('/api/interface-inspection',{operation:'cancel',job_id:jobId});}catch{} }
  el('inspectionClose').onclick=()=>{void cancel();el('inspectionResults').replaceChildren();dialog.close();};
  dialog.addEventListener('cancel',()=>{void cancel();el('inspectionResults').replaceChildren();});
  el('inspectionStop').onclick=()=>{void cancel();el('inspectionStatus').textContent='Cancellation requested. An in-flight capture or provider request may finish; completed results are kept.';};
  el('inspectionStart').onclick=async()=>{
    if(running)return;
    running=true;stop=false;el('inspectionStart').disabled=true;el('inspectionStop').disabled=false;
    const panel=el('inspectionPanel').value;
    const transmit=el('inspectionTransmit').checked,scope=el('inspectionScope').value,focus=el('inspectionFocus').value;
    const deadline=Date.now()+1020000;
    el('inspectionResults').replaceChildren();
    try{
      el('inspectionStatus').textContent='Starting inspection job…';
      const started=await api('/api/interface-inspection',{operation:'start',request:{panel,scope,focus},transmit});
      jobId=started.job_id;if(stop)await cancel();
      const seen=new Set();
      while(Date.now()<deadline){
        const job=await api('/api/interface-inspection',{operation:'status',job_id:jobId});
        if(!dialog.open){await cancel();break;}
        for(const result of job.results||[]){
        const panel=result.requested_panel;if(seen.has(panel))continue;seen.add(panel);
        const section=document.createElement('section'),heading=document.createElement('h3'),report=document.createElement('pre');
        heading.textContent=panel+' · '+result.status+' · '+result.assessment_mode;
        report.textContent=result.analysis||'No analysis completed.';
        report.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';
        section.append(heading,report);
        const details=document.createElement('details'),summary=document.createElement('summary'),evidence=document.createElement('pre');
        summary.textContent='Capture evidence and limitations';evidence.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';
        evidence.textContent=JSON.stringify({...result,analysis:undefined,visible_text:undefined,accessibility:undefined,screenshots:(result.screenshots||[]).map(s=>({section:s.section,reference:s.reference}))},null,2);
        details.append(summary,evidence);section.append(details);
        for(const shot of result.screenshots||[]){if(!/^\/api\/interface-inspection\/image\/[a-f0-9]{32}$/.test(shot.reference||''))continue;const image=document.createElement('img');image.src=shot.reference;image.alt=panel+' masked inspection capture';image.style.width='100%';section.append(image);setTimeout(()=>{image.removeAttribute('src');image.remove();},300000);}
        el('inspectionResults').append(section);
        }
        el('inspectionStatus').textContent=job.status==='running'?`${seen.size}/${job.panels.length} panels finished · ${job.phase==='archiving'?'Saving inspection report':job.current_panel?'Capturing and analysing '+job.current_panel:'Consolidating findings'}${stop?' · stopping after current operation':''}`:`${job.status} · ${seen.size}/${job.panels.length} panels finished`;
        if(job.status!=='running'){
          const review=document.createElement('section'),heading=document.createElement('h3'),body=document.createElement('pre');
          heading.textContent='Whole inspection review · '+job.review_status;
          const archived=document.createElement('p');archived.textContent=job.archive?.status==='archived'?'Archived in Project Jarvis · '+job.archive.inspection_id:job.archive?.error||'Archive status not yet confirmed.';review.append(archived);
          body.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';
          body.textContent=(job.review||'No visual review completed.')+'\n\n'+(job.errors||[]).join('\n')+'\n\nNot completed: '+job.panels.filter(p=>!seen.has(p)).join(', ');
          review.append(heading,body);el('inspectionResults').prepend(review);break;
        }
        await new Promise(resolve=>setTimeout(resolve,1000));
      }
      if(Date.now()>=deadline){await cancel();el('inspectionStatus').textContent='Inspection timed out. Completed results retained.';}
    }catch(e){el('inspectionStatus').textContent='Inspection failed: '+e.message;}
    finally{running=false;jobId=null;el('inspectionStart').disabled=false;el('inspectionStop').disabled=true;}
  };
  window.startInterfaceInspection=request=>{if(running){if(!dialog.open)dialog.showModal();return;}window.openInterfaceInspection(request);el('inspectionStart').click();};
  const button=document.createElement('button');button.textContent='INSPECT INTERFACE';button.onclick=()=>window.openInterfaceInspection();
  document.querySelector('.conversation-actions').append(button);
  const originalSend=send;
  send=async function(text,...args){
    const match=String(text).trim().match(/^(?:hey jarvis[, ]+)?(?:(?:can|could|would) you |please )?(?:inspect|review|analyse|analyze|look at)(?: the| my| your)? (command(?: centre| center)?|communications|system(?: status)?|mission(?: log)?|focus(?: and tasks)?|projects|memory|files|web|diagrams|settings|changes|maps|(?:(?:whole|entire) (?:interface|application|app)|all (?:interfaces|panels)))(?: page| panel)?(?: and (?:suggest improvements|recommend improvements|(?:analyse|analyze) it))?[.!?]*$/i);
    // An inspection can send pictures of the interface to the AI provider: it obeys the owner's switch for it and
    // the emergency stop. When it is not allowed here, the words go to the Core, which refuses or asks first.
    if(match&&(typeof JarvisPermissions==='undefined'||JarvisPermissions.windowMay(state.data,'inspect_interface'))){const panel=match[1].toLowerCase().split(' ')[0];window.startInterfaceInspection({panel:['whole','entire','all'].includes(panel)?'all':panel,scope:'full_panel',focus:'Review readability, contrast, spacing, alignment, navigation, consistency, accessibility, information density and status clarity. Suggest improvements; do not apply changes.'});return true;}
    return originalSend(text,...args);
  };
})();
