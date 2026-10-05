"""Fresh briefing snapshots and bounded action receipts; no model inference."""
import datetime
from email.utils import parsedate_to_datetime
import re
import time

import permissions


def stamp(value):
    return datetime.datetime.fromtimestamp(value,datetime.timezone.utc).astimezone().isoformat(timespec='seconds')


def command(text):
    clean=text.strip().rstrip('.!?').lower()
    if re.fullmatch(r"(?:(?:please )?(?:give me|show me|prepare|read)(?: my| a| the)? )?(?:daily briefing|morning briefing|today's briefing)|what(?:'s| is) (?:happening|on) today|what happens today",clean):
        return 'daily_briefing',{}
    if re.fullmatch(r"(?:what are|show|list)(?: my| the)?(?: active)? projects",clean):
        return 'project_catalog',{}
    return None


def briefing(readers):
    sections={}
    for name,read in readers.items():
        try:
            raw=read()
            rows=raw['results'] if name=='news' else raw
            if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows):
                raise ValueError('Invalid source response')
            checked=time.time()
            section={'status':'checked' if rows else 'checked_empty','checked_at':checked,'total':len(rows),'items':rows[:5 if name=='news' else 8],'limited':len(rows)>(5 if name=='news' else 8)}
            if name=='news':
                retrieved=raw.get('retrieved_at')
                try:retrieved_at=datetime.datetime.fromisoformat(retrieved).timestamp()
                except (TypeError,ValueError):retrieved_at=None
                section.update(retrieved_at=retrieved,cached=bool(raw.get('cached')))
                if retrieved_at is None:section['status']='unverified'
                elif raw.get('cached') or checked-retrieved_at>300 or retrieved_at>checked+60:section['status']='stale'
                section['items']=[{**r,'publication_status':publication_status(r.get('published'),checked)} for r in section['items']]
            sections[name]=section
        except Exception as exc:
            sections[name]={'status':'failed','checked_at':time.time(),'items':[],'error_code':type(exc).__name__}
    sections['calendar']={'status':'unavailable','items':[],'scope':'No calendar integration is connected to this briefing.'}
    return {'status':'partial' if any(s['status'] in ('failed','unverified','stale') for s in sections.values()) else 'checked',
            'sections':sections,'generated_at':time.time(),
            'scope':'Saved outstanding tasks, saved reminders and project registry; not a complete calendar. News is feed metadata, not independently verified reporting.'}


def publication_status(value,now):
    try:
        date=parsedate_to_datetime(value)
        if date.tzinfo is None:return 'publication date unverified'
        age=now-date.timestamp()
        return 'older than 48 hours' if age>172800 else 'future date; unverified' if age < -300 else 'published within 48 hours'
    except (TypeError,ValueError,OverflowError):return 'publication date unverified'


def briefing_details(result):
    lines=['Briefing checked at '+stamp(result['generated_at'])+'.',result['scope']]
    for name,s in result['sections'].items():
        label=name.capitalize()
        if s['status']=='failed':lines.append(label+': could not check ('+s['error_code']+').');continue
        if s['status']=='unavailable':lines.append(label+': unavailable. '+s['scope']);continue
        when=' Checked at '+stamp(s['checked_at'])+'.'
        if s['status']=='checked_empty':lines.append(label+': nothing found in this source.'+when);continue
        lines.append(label+': '+s['status']+'.'+when)
        if name=='news':
            lines.append('Feed retrieved: '+str(s.get('retrieved_at') or 'unknown')+'. Headlines below are source reports, not proven facts.')
        for row in s['items']:
            title=str(row.get('title') or row.get('name') or row.get('body') or 'Untitled')
            if name=='news':lines.append('• '+title+' — '+str(row.get('source') or 'publisher unknown')+'; '+str(row.get('published') or 'date unknown')+' ('+row['publication_status']+'). '+str(row.get('url','')))
            elif name=='reminders':lines.append('• '+title+' — '+('already due' if row.get('due',0)<=s['checked_at'] else 'due '+stamp(row['due']))+'.')
            else:lines.append('• '+title)
        if s.get('limited'):lines.append(f"Showing {len(s['items'])} of {s['total']} records.")
    return '\n'.join(lines)


def receipt(name,result):
    if result.get('error'):return 'failed'
    status=result.get('status')
    if status:return str(status)
    if name=='save_item' and result.get('id'):return 'saved'
    if name=='create_file' and result.get('url'):return 'file created'
    return 'result returned; completion not inferred'


ACTION_TOOLS=permissions.ACTION_TOOLS  # which tools' results count as receipts: one table, permissions.py


def action_guard(text,events):
    # Deliberately bounded: this catches common completion wording, not every
    # possible unsupported claim. All matching replies use actual receipts.
    claim=re.search(r"\b(?:i(?:'ve| have)?|we(?:'ve| have)?)\s+(?:successfully\s+)?(?:saved|created|scheduled|cancelled|canceled|deleted|updated|applied|opened|launched|completed)\b|\b(?:timer|reminder|note|file|change|update|inspection)\b[^.!?\n]{0,50}\b(?:has been|was|is)\s+(?:successfully\s+)?(?:saved|created|scheduled|cancelled|canceled|deleted|updated|applied|completed)\b",text,re.I)
    if not claim:return text
    rows=[e for e in events if e['event'] in ('tool.completed','tool.failed') and e['data']['name'] in ACTION_TOOLS]
    if not rows:return 'No matching action result was recorded for this request. Completion is not confirmed.'
    return 'Action evidence for this request:\n'+'\n'.join(e['data']['name'].replace('_',' ')+': '+('failed' if e['event']=='tool.failed' else receipt(e['data']['name'],e['data']['result']))+'. Checked at '+stamp(e['data'].get('checked_at',time.time()))+'.' for e in rows)+'\nRequested or awaiting approval does not mean completed. These receipts cover only the listed actions.'


def evidence(events):
    rows=[]
    for e in events:
        if e['event'] not in ('tool.completed','tool.failed'):continue
        data=e['data'];result=data.get('result',{})
        rows.append({'tool':data['name'],'status':'failed' if e['event']=='tool.failed' else receipt(data['name'],result),'checked_at':data.get('checked_at'),'scope':result.get('scope','Only this tool result; not proof of unrelated claims.')})
    return rows


def describe_briefing(result):
    parts=["Here's your briefing, Sir."]
    sections=result.get('sections',{})
    for name in ('tasks','reminders','projects'):
        section=sections.get(name,{})
        if section.get('status')=='failed':
            parts.append("I couldn't check your "+name+" just now.");continue
        rows=section.get('items',[])
        if not rows:
            parts.append({'tasks':"You have no outstanding tasks saved.",'reminders':"You have no reminders saved.",'projects':"You have no projects saved."}[name]);continue
        titles=[str(row.get('title') or row.get('name') or row.get('body') or 'Untitled') for row in rows[:3]]
        parts.append({'tasks':'Your saved tasks are: ','reminders':'Your saved reminders are: ','projects':'Your saved projects are: '}[name]+'; '.join(titles)+'.')
        remaining=section.get('total',len(rows))-len(titles)
        if remaining>0:parts.append(f'There are {remaining} more {name} in the details.')
    news=sections.get('news',{})
    if news.get('status')=='failed':parts.append("I couldn't get the news just now.")
    elif news.get('status')=='checked_empty':parts.append("The news feed didn't return any headlines.")
    else:
        if news.get('status') in ('stale','unverified'):parts.append("I couldn't confirm that the news feed is up to date.")
        rows=news.get('items',[])[:3]
        if rows:parts.append("Here are a few headlines from the news feed.")
        for row in rows:
            title=str(row.get('title') or 'Untitled headline')
            source=str(row.get('source') or '')
            if source and title.endswith(' - '+source):title=title[:-len(' - '+source)]
            prefix='An older headline: ' if row.get('publication_status')=='older than 48 hours' else ''
            parts.append(prefix+(source+' reports: ' if source else '')+title+'.')
    parts.append("I can't check your calendar yet. Sources and check times are in the details on screen.")
    # Stored titles can themselves contain pasted links; never read raw URLs aloud.
    return re.sub(r'https?://\S+','', ' '.join(parts))
