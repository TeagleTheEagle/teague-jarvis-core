(()=>{
  let projects=[],active=localStorage.getItem('jarvis.workspace')||'',diagram=null;
  const panel=document.createElement('section');panel.className='panel workspace-projects';panel.style.cssText='padding:20px;margin:16px 0';
  const heading=document.createElement('h2');heading.textContent='PROJECT WORKSPACES';
  const controls=document.createElement('div');controls.style.cssText='display:flex;gap:10px;flex-wrap:wrap;align-items:center';
  const select=document.createElement('select');select.setAttribute('aria-label','Active project');
  const name=document.createElement('input');name.placeholder='New project name';name.maxLength=100;name.setAttribute('aria-label','New project name');
  const resources=document.createElement('select');resources.setAttribute('aria-label','Saved work to link');resources.style.maxWidth='350px';
  const list=document.createElement('div');const status=document.createElement('p');status.textContent='Choose a project, then link conversations and saved work. Original records stay in place.';
  function button(label,fn,parent=controls){const b=document.createElement('button');b.type='button';b.textContent=label;b.onclick=async()=>{try{await fn();}catch(e){toast(e.message,true);}};parent.append(b);return b;}
  controls.append(select,name);button('CREATE PROJECT',async()=>{const r=await api('/api/workspaces',{action:'create',name:name.value});active=r.id;localStorage.setItem('jarvis.workspace',active);name.value='';await reload();});
  button('LINK CURRENT CHAT',async()=>{await mutate({kind:'conversation',ref:state.conversation,title:state.data?.conversations.find(c=>c.id===state.conversation)?.title||'Project conversation'});});
  controls.append(resources);button('LINK SAVED WORK',async()=>{if(!resources.value)throw Error('Choose a saved record.');const [kind,ref]=JSON.parse(resources.value);await mutate({kind,ref});});
  button('SAVE CURRENT DIAGRAM',async()=>{if(!diagram)throw Error('Generate a diagram first.');await mutate({kind:'diagram',ref:crypto.randomUUID(),title:diagram.title,content:diagram});});
  panel.append(heading,controls,status,list);document.querySelector('#projectsView').append(panel);
  const renderDiagram=showSuitDiagram;showSuitDiagram=function(r){diagram=r;return renderDiagram(r);};
  async function mutate(args){if(!active)throw Error('Choose a project first.');await api('/api/workspaces',{action:'link',project:active,...args});await reload();}
  select.onchange=()=>{active=select.value;localStorage.setItem('jarvis.workspace',active);render();};
  function render(){select.replaceChildren(new Option('Choose project',''));projects.forEach(p=>select.add(new Option(p.name,p.id)));select.value=active;list.replaceChildren();const project=projects.find(p=>p.id===active);if(!project)return;
    const caption=document.createElement('p');caption.textContent=project.links.length+' linked records · saved on this computer';list.append(caption);
    project.links.forEach(item=>{const row=document.createElement('div');row.style.cssText='display:flex;gap:12px;align-items:center;border-top:1px solid var(--soft-line,#8ac9e366);padding:10px 0';const label=document.createElement('span');label.textContent=item.kind.toUpperCase()+' · '+item.title;label.style.flex='1';row.append(label);
      button('OPEN',async()=>{if(state.busy)throw Error('Wait for the current reply to finish.');if(item.kind==='conversation'){state.conversation=item.ref;localStorage.setItem('jarvis.conversation',item.ref);state.attachment=null;renderAttachment();view('command');await loadHistory();await refresh();}else if(item.kind==='diagram'){showSuitDiagram(JSON.parse(item.content));view('diagrams');}else{view(item.kind==='document'?'files':item.kind==='task'?'command':'memory');}},row);
      button('UNLINK',async()=>{await mutate({action:'unlink',kind:item.kind,ref:item.ref});},row);list.append(row);
    });
  }
  async function reload(){projects=(await api('/api/workspaces')).projects;render();const d=await api('/api/state');resources.replaceChildren(new Option('Select note, task, or document',''));[['note',d.notes],['task',d.tasks],['document',d.documents]].forEach(([kind,items])=>(items||[]).forEach(i=>resources.add(new Option(kind+': '+(i.name||i.body).slice(0,75),JSON.stringify([kind,i.id])))));}
  button('REFRESH LIST',reload);reload().catch(e=>toast('Projects: '+e.message,true));
})();
