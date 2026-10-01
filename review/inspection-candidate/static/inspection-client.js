'use strict';
(() => {
  if(window.JARVIS_INSPECTION)return;
  const panels=['command','communications','system','mission','focus','projects','memory','files','web','diagrams','settings','changes','maps'];
  const dialog=document.createElement('dialog');dialog.setAttribute('aria-label','Interface inspection');
  dialog.innerHTML='<h2>Inspect JARVIS</h2><p>Inspect a separate read-only copy. Your current page stays in place. Private saved text is masked; this reviews layout and controls.</p><label>Panel <select id="inspectionPanel"></select></label><label>Coverage <select id="inspectionScope"><option value="viewport">Viewport</option><option value="full_panel">Bounded panel sections</option></select></label><label>Focus <input id="inspectionFocus" maxlength="2000"></label><p id="inspectionRecipient"></p><label><input type="checkbox" id="inspectionTransmit"> Send masked captures and my focus question to that provider for this inspection. Provider retention policies apply.</label><p>Without this checkbox, captures and the DOM report stay local. Captures expire after five minutes. Reports are not saved automatically.</p><button id="inspectionStart">INSPECT</button><button id="inspectionStop" disabled>STOP AFTER CURRENT PANEL</button><button id="inspectionClose">CLOSE</button><p id="inspectionStatus" role="status"></p><div id="inspectionResults"></div>';
  document.body.append(dialog);
  const el=id=>dialog.querySelector('#'+id);
  panels.forEach(p=>el('inspectionPanel').add(new Option(p,p)));
  el('inspectionPanel').add(new Option('Whole interface (sequential)','all'));
  let running=false,stop=false;
  window.openInterfaceInspection=(request={})=>{
    if(running){dialog.showModal();return;}
    el('inspectionPanel').value=panels.includes(request.panel)?request.panel:'command';
    if(request.panel==='all')el('inspectionPanel').value='all';
    el('inspectionScope').value=request.scope==='full_panel'?'full_panel':'viewport';
    el('inspectionFocus').value=typeof request.focus==='string'?request.focus.slice(0,2000):'';
    el('inspectionTransmit').checked=false;
    el('inspectionRecipient').textContent='Analysis recipient: '+(state.data?.capabilities?.vision_provider||'configured vision provider (availability not verified)');
    if(!dialog.open)dialog.showModal();
  };
  el('inspectionClose').onclick=()=>{stop=true;el('inspectionResults').replaceChildren();dialog.close();};
  dialog.addEventListener('cancel',()=>{stop=true;el('inspectionResults').replaceChildren();});
  el('inspectionStop').onclick=()=>{stop=true;el('inspectionStatus').textContent='Stopping after the current panel. An image already submitted cannot be recalled.';};
  el('inspectionStart').onclick=async()=>{
    if(running)return;
    running=true;stop=false;el('inspectionStart').disabled=true;el('inspectionStop').disabled=false;
    const list=el('inspectionPanel').value==='all'?panels:[el('inspectionPanel').value];
    const transmit=el('inspectionTransmit').checked,scope=el('inspectionScope').value,focus=el('inspectionFocus').value;
    const deadline=Date.now()+300000;
    el('inspectionResults').replaceChildren();
    try{
      for(const panel of list){
        if(stop||Date.now()>deadline){el('inspectionStatus').textContent='Inspection stopped; remaining panels skipped.';break;}
        el('inspectionStatus').textContent='Rendering '+panel+' in isolation…';
        const result=await api('/api/interface-inspection',{request:{panel,scope,focus},transmit});
        if(stop){el('inspectionStatus').textContent='Stopped. Current request finished; remaining panels skipped.';break;}
        const section=document.createElement('section'),heading=document.createElement('h3'),report=document.createElement('pre');
        heading.textContent=panel+' · '+result.assessment_mode;
        report.textContent=result.analysis||'No analysis completed.';
        report.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';
        section.append(heading,report);
        const details=document.createElement('details'),summary=document.createElement('summary'),evidence=document.createElement('pre');
        summary.textContent='Capture evidence and limitations';evidence.style.cssText='white-space:pre-wrap;overflow-wrap:anywhere';
        evidence.textContent=JSON.stringify({...result,analysis:undefined,visible_text:undefined,accessibility:undefined,screenshots:(result.screenshots||[]).map(s=>({section:s.section,reference:s.reference}))},null,2);
        details.append(summary,evidence);section.append(details);
        for(const shot of result.screenshots||[]){if(!/^\/api\/interface-inspection\/image\/[a-f0-9]{32}$/.test(shot.reference||''))continue;const image=document.createElement('img');image.src=shot.reference;image.alt=panel+' masked inspection capture';image.style.width='100%';section.append(image);setTimeout(()=>{image.removeAttribute('src');image.remove();},300000);}
        el('inspectionResults').append(section);
        el('inspectionStatus').textContent=result.errors?.length?'Finished with limitations.':'Inspection report ready.';
      }
    }catch(e){el('inspectionStatus').textContent='Inspection failed: '+e.message;}
    finally{running=false;el('inspectionStart').disabled=false;el('inspectionStop').disabled=true;}
  };
  const button=document.createElement('button');button.textContent='INSPECT INTERFACE';button.onclick=()=>window.openInterfaceInspection();
  document.querySelector('.conversation-actions').append(button);
  const originalSend=send;
  send=async function(text,...args){
    const match=String(text).trim().match(/^(?:hey jarvis[, ]+)?(?:inspect|analyse|analyze|look at)(?: the)? (command(?: centre| center)?|communications|system(?: status)?|mission(?: log)?|focus(?: and tasks)?|projects|memory|files|web|diagrams|settings|changes|maps|whole interface)(?: page| panel)?(?: and (?:analyse|analyze) it)?[.!?]*$/i);
    if(match){const panel=match[1].toLowerCase().split(' ')[0];window.openInterfaceInspection({panel:panel==='whole'?'all':panel});el('inspectionStart').click();return true;}
    return originalSend(text,...args);
  };
})();
