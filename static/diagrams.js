// Shared concept viewer for tool calls and the diagram form.
function showSuitDiagram(result){
  const root=document.querySelector('#diagramResult');root.replaceChildren();
  const title=document.createElement('h3');title.textContent=result.title+' · '+result.view;
  const bar=document.createElement('div');bar.style.cssText='display:flex;gap:8px;flex-wrap:wrap;margin:16px 0';
  const frame=document.createElement('div');frame.style.cssText='background:#06141d;border:1px solid #328399;overflow:hidden;width:100%;touch-action:none';
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 1000 700');svg.setAttribute('role','img');svg.setAttribute('aria-label',title.textContent);svg.style.cssText='width:100%;height:min(72vh,850px);display:block;cursor:grab';
  function add(tag,attrs={},text=''){const el=document.createElementNS(svg.namespaceURI,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v));el.textContent=text;svg.append(el);return el;}
  add('style',{},'path,circle,rect,line{stroke:#59ddec;stroke-width:2;fill:#102d3e}text{fill:#a9efff;font:16px sans-serif}line{fill:none;opacity:.55}');
  add('rect',{width:1000,height:700,style:'fill:#06141d;stroke:none'});
  for(let x=0;x<1000;x+=50)add('line',{x1:x,x2:x,y1:0,y2:700,style:'opacity:.07'});
  for(let y=0;y<700;y+=50)add('line',{x1:0,x2:1000,y1:y,y2:y,style:'opacity:.07'});
  const side=result.view==='side';
  if(result.view!=='system'){
    const paths=side?[
      'M475 65 L525 65 L545 95 L530 135 L478 135 L465 105 Z',
      'M477 145 L535 145 L555 220 L525 315 L480 315 L463 230 Z',
      'M480 165 L515 175 L520 275 L500 360 L472 350 L482 270 Z',
      'M485 325 L528 325 L535 430 L512 460 L470 450 Z',
      'M477 460 L512 470 L510 575 L550 595 L550 615 L472 615 Z'
    ]:[
      'M470 60 L530 60 L546 90 L535 135 L465 135 L454 90 Z',
      'M440 150 L500 140 L560 150 L575 225 L550 295 L450 295 L425 225 Z',
      'M453 305 L547 305 L560 355 L520 375 L500 355 L480 375 L440 355 Z',
      'M428 155 L395 155 L365 245 L397 265 L437 210 Z',
      'M572 155 L605 155 L635 245 L603 265 L563 210 Z',
      'M365 257 L393 278 L375 365 L345 355 Z',
      'M635 257 L607 278 L625 365 L655 355 Z',
      'M445 375 L482 389 L478 480 L431 480 Z',
      'M555 375 L518 389 L522 480 L569 480 Z',
      'M431 490 L478 490 L469 590 L412 590 Z',
      'M569 490 L522 490 L531 590 L588 590 Z',
      'M412 595 L469 595 L475 620 L398 620 Z',
      'M588 595 L531 595 L525 620 L602 620 Z'
    ];paths.forEach(d=>add('path',{d}));
  }else add('rect',{x:425,y:280,width:150,height:90,rx:8});
  const components=result.components||['Sensors','Power core','Mobility'];
  components.forEach((label,i)=>{
    if(result.view!=='system'){
      if(label==='Power core')add('circle',{cx:side?537:500,cy:215,r:side?12:25,style:'fill:#3fcce0'});
      if(label==='Sensors')add('path',{d:side?'M516 88 L542 95 L530 105 L515 102 Z':'M465 90 L495 97 L505 97 L535 90 L530 107 L505 112 L495 112 L470 107 Z'});
      if(label==='Backpack')add('rect',{x:side?430:550,y:170,width:30,height:105,rx:6});
      if(label==='Cooling')for(let j=0;j<4;j++)add('line',{x1:485,y1:255+j*8,x2:515,y2:255+j*8});
      if(label==='Communications')add('path',{d:'M480 65 L475 30 L470 30'});
      if(label==='Mobility')add('circle',{cx:side?490:455,cy:485,r:10});
    }
    const right=i%2,x=right?740:60,y=155+Math.floor(i/2)*155;
    add('line',{x1:right?570:430,y1:y+10,x2:right?730:260,y2:y+10});
    add('text',{x,y},label);
  });
  if(result.view==='system')add('text',{x:500,y:330,'text-anchor':'middle'},'Suit controller');
  add('text',{x:35,y:675,style:'font:12px monospace;fill:#6598ab'},'JARVIS / CONCEPT STUDY / '+result.view.toUpperCase());
  let zoom=1,px=0,py=0,drag;
  const redraw=()=>svg.setAttribute('viewBox',`${px} ${py} ${1000/zoom} ${700/zoom}`);
  function button(label,fn){const b=document.createElement('button');b.type='button';b.textContent=label;b.onclick=fn;bar.append(b);}
  button('ZOOM +',()=>{zoom=Math.min(4,zoom*1.25);redraw();});button('ZOOM −',()=>{zoom=Math.max(1,zoom/1.25);redraw();});button('RESET VIEW',()=>{zoom=1;px=py=0;redraw();});
  button('FULLSCREEN',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await frame.requestFullscreen();}catch(e){toast('Fullscreen is unavailable in this browser.',true);}});
  button('DOWNLOAD SVG',()=>{const copy=svg.cloneNode(true);copy.removeAttribute('style');copy.setAttribute('viewBox','0 0 1000 700');copy.setAttribute('width','1000');copy.setAttribute('height','700');const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(copy)],{type:'image/svg+xml'}));const a=document.createElement('a');a.href=url;a.download='jarvis-'+result.view+'.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  svg.onpointerdown=e=>{drag={x:e.clientX,y:e.clientY,px,py};svg.setPointerCapture(e.pointerId);};
  svg.onpointermove=e=>{if(!drag)return;const scale=Math.min(svg.clientWidth/1000,svg.clientHeight/700)*zoom;px=drag.px-(e.clientX-drag.x)/scale;py=drag.py-(e.clientY-drag.y)/scale;redraw();};svg.onpointerup=svg.onpointercancel=()=>drag=null;
  frame.append(svg);const note=document.createElement('p');note.textContent='Concept illustration with preset geometry. Drag to pan. Component keywords: sensors, power core, cooling, communications, mobility, backpack.';root.append(title,bar,frame,note);
}
document.querySelector('#diagramForm').onsubmit=async e=>{e.preventDefault();const b=e.currentTarget.querySelector('[type="submit"]')||e.currentTarget.querySelector('button');b.disabled=true;try{const result=await api('/api/tool',{name:'suit_diagram',args:{request:document.querySelector('#diagramRequest').value,view:document.querySelector('#diagramView').value}});showSuitDiagram(result);}catch(err){toast(err.message,true);}finally{b.disabled=false;}};
