(() => {
  const get=id=>document.getElementById(id);
  function update(){
    const now=new Date();
    const parts=new Intl.DateTimeFormat('en-AU',{hour:'2-digit',minute:'2-digit',hour12:true}).formatToParts(now);
    get('clock').textContent=parts.filter(p=>['hour','minute','literal'].includes(p.type)).map(p=>p.value).join('').trim();
    get('clock').dateTime=now.toISOString();
    get('clockPeriod').textContent=parts.find(p=>p.type==='dayPeriod')?.value.toUpperCase()||'';
    get('weekday').textContent=now.toLocaleDateString('en-AU',{weekday:'long'});
    get('date').textContent=now.toLocaleDateString('en-AU',{day:'numeric',month:'long',year:'numeric'});
    get('date').dateTime=[now.getFullYear(),String(now.getMonth()+1).padStart(2,'0'),String(now.getDate()).padStart(2,'0')].join('-');
    const zone=Intl.DateTimeFormat().resolvedOptions().timeZone||'Local';
    get('clockZone').textContent=zone.replaceAll('_',' ')+' · time zone';
  }
  function label(){get('clockLocation').textContent=localStorage.getItem('jarvis.locationLabel')||'Set location ↗';}
  get('clockLocation').onclick=()=>{get('clockLocationInput').value=localStorage.getItem('jarvis.locationLabel')||'';get('clockLocationDialog').showModal();};
  get('clockLocationForm').onsubmit=e=>{e.preventDefault();const value=get('clockLocationInput').value.trim();if(value)localStorage.setItem('jarvis.locationLabel',value);else localStorage.removeItem('jarvis.locationLabel');label();get('clockLocationDialog').close();};
  update();label();setInterval(update,1000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)update();});
})();
