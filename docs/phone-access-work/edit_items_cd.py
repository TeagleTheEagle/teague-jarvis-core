"""Items C (screen analysis from the phone) and D (location with a question) of docs/PHONE-ACCESS-PLAN.md.
Byte-exact edits; static/app.js is a mixed-ending file and is edited at the byte level with CRLF for new lines."""
import pathlib
import sys

REPO = pathlib.Path(r"C:\Users\jonny\JARVIS-claude-workspace\repo")


def edit(path, replacements):
    p = REPO / path
    data = p.read_bytes()
    crlf, lf = data.count(b"\r\n"), data.count(b"\n") - data.count(b"\r\n")
    if crlf and lf:
        sys.exit(path + " is mixed; use edit_bytes")
    ending = "\r\n" if crlf else "\n"
    text = data.decode("utf-8").replace("\r\n", "\n")
    for old, new in replacements:
        n = text.count(old)
        if n != 1:
            sys.exit(f"{path}: expected exactly one match, found {n} for:\n{old[:200]}")
        text = text.replace(old, new)
    p.write_bytes(text.replace("\n", ending).encode("utf-8"))
    print(f"{path}: {len(replacements)} edits")


def edit_bytes(path, replacements):
    """For a mixed-ending file: old and new are given with \\n; the old text is matched with CRLF endings and the
    new text is written with CRLF endings, so only the replaced lines change."""
    p = REPO / path
    data = p.read_bytes()
    for old, new in replacements:
        old_b = old.replace("\n", "\r\n").encode("utf-8")
        new_b = new.replace("\n", "\r\n").encode("utf-8")
        n = data.count(old_b)
        if n != 1:
            sys.exit(f"{path}: expected exactly one match, found {n} for:\n{old[:200]}")
        data = data.replace(old_b, new_b)
    p.write_bytes(data)
    print(f"{path}: {len(replacements)} byte edits")


# ---------------------------------------------------------------- item D: maps.py
edit("maps.py", [
    (
        "def directions(origin, destination, mode='DRIVE'):\n"
        "    start, end = waypoint(origin), waypoint(destination)\n"
        "    if mode not in ('DRIVE', 'WALK', 'BICYCLE'):\n"
        "        raise ValueError('Choose driving, walking, or cycling.')\n"
        "    if origin.strip().lower() in ('current location', 'my location', 'here'):\n"
        "        return {'needs_location': True, 'destination': destination, 'mode': mode,\n"
        "                'message': 'Open Maps and choose Use my location or enter a starting address, then calculate the route. Location has not been accessed and no route is calculated yet.'}\n",
        "def directions(origin, destination, mode='DRIVE', location=None):\n"
        "    \"\"\"location (1.0.17, docs/PHONE-ACCESS-1.0.17.md item D): the position a paired device sent with its question\n"
        "    ({'lat', 'lon', 'label'?}); it is the starting point when the owner says \"from here\". Used for this route only.\"\"\"\n"
        "    start, end = waypoint(origin), waypoint(destination)\n"
        "    if mode not in ('DRIVE', 'WALK', 'BICYCLE'):\n"
        "        raise ValueError('Choose driving, walking, or cycling.')\n"
        "    here = origin.strip().lower() in ('current location', 'my location', 'here')\n"
        "    map_origin = origin\n"
        "    if here and location:\n"
        "        start = waypoint(f\"{float(location['lat'])},{float(location['lon'])}\")\n"
        "        map_origin = f\"{float(location['lat'])},{float(location['lon'])}\"\n"
        "        origin = str(location.get('label') or '').strip() or 'your location'\n"
        "    elif here:\n"
        "        return {'needs_location': True, 'destination': destination, 'mode': mode,\n"
        "                'message': 'Open Maps and choose Use my location or enter a starting address, then calculate the route. Location has not been accessed and no route is calculated yet.'}\n",
    ),
    (
        "            'url': 'https://www.google.com/maps/dir/?' + urllib.parse.urlencode({'api': 1, 'origin': origin, 'destination': destination, 'travelmode': {'DRIVE': 'driving', 'WALK': 'walking', 'BICYCLE': 'bicycling'}[mode]})}\n",
        "            'url': 'https://www.google.com/maps/dir/?' + urllib.parse.urlencode({'api': 1, 'origin': map_origin, 'destination': destination, 'travelmode': {'DRIVE': 'driving', 'WALK': 'walking', 'BICYCLE': 'bicycling'}[mode]})}\n",
    ),
])

# ---------------------------------------------------------------- item D: wearables/service.py
edit("wearables/service.py", [
    (
        "class Service:\n",
        "def _location(value):\n"
        "    \"\"\"A device's position sent with a question (1.0.17, docs/PHONE-ACCESS-1.0.17.md item D): checked here, given to\n"
        "    that one answer and to directions, kept by the Core nowhere.\"\"\"\n"
        "    if not isinstance(value,dict) or set(value)-{'lat','lon','accuracy_m','label'} or 'lat' not in value or 'lon' not in value: raise ValueError('Invalid location.')\n"
        "    lat,lon=value['lat'],value['lon']\n"
        "    if any(isinstance(v,bool) or not isinstance(v,(int,float)) for v in (lat,lon)) or not -90<=lat<=90 or not -180<=lon<=180: raise ValueError('Invalid location.')\n"
        "    out={'lat':float(lat),'lon':float(lon)}\n"
        "    if 'accuracy_m' in value:\n"
        "        accuracy=value['accuracy_m']\n"
        "        if isinstance(accuracy,bool) or not isinstance(accuracy,(int,float)) or not 0<=accuracy<=100000: raise ValueError('Invalid location.')\n"
        "        out['accuracy_m']=float(accuracy)\n"
        "    if 'label' in value:\n"
        "        label=value['label']\n"
        "        if not isinstance(label,str) or len(label)>80 or re.search(r'[\\x00-\\x1f]',label): raise ValueError('Invalid location.')\n"
        "        out['label']=label.strip()\n"
        "    return out\n"
        "\n"
        "\n"
        "class Service:\n",
    ),
    (
        "                if set(body)-{'text','image','conversation'}: raise ValueError('Unknown fields.')\n"
        "                text=body.get('text'); conversation=body.get('conversation',self.prefix+'local')\n",
        "                if set(body)-{'text','image','conversation','location'}: raise ValueError('Unknown fields.')\n"
        "                text=body.get('text'); conversation=body.get('conversation',self.prefix+'local')\n"
        "                location=_location(body['location']) if 'location' in body else None\n",
    ),
    (
        "                        result=self.app.start_run({'text':text,'conversation':conversation,**({'attachment':attachment['id']} if attachment else {})},wearable=True,device=self.device_id,writes=self.writes,tools=self.tools)\n",
        "                        result=self.app.start_run({'text':text,'conversation':conversation,**({'attachment':attachment['id']} if attachment else {})},wearable=True,device=self.device_id,writes=self.writes,tools=self.tools,location=location)\n",
    ),
])

# ---------------------------------------------------------------- item D: device_gateway.py (the showable sentence)
edit("device_gateway.py", [
    (
        "    'Supply only run_id and after.', LOCKED_MESSAGE))\n",
        "    'Supply only run_id and after.', 'Invalid location.', 'Announcement limit reached. Wait one minute.', LOCKED_MESSAGE))\n",
    ),
])

# ---------------------------------------------------------------- item C: assistant_capabilities.py (CRLF)
edit("assistant_capabilities.py", [
    (
        "class Controls:\n"
        "    def __init__(self):\n"
        "        self.lock, self.pending = threading.Lock(), {}\n"
        "\n"
        "    def request(self, action, run, timeout=30):\n"
        "        if action not in CONTROL_ACTIONS or run is None: raise ValueError('A connected conversation is required.')\n",
        "class Controls:\n"
        "    # A paired device's question (1.0.17, docs/PHONE-ACCESS-1.0.17.md item C) is answered by the PC window through\n"
        "    # /api/control-requests, which it reads every few seconds: it gets longer than the window's own 30 s.\n"
        "    DEVICE_TIMEOUT = 45\n"
        "\n"
        "    def __init__(self):\n"
        "        self.lock, self.pending = threading.Lock(), {}\n"
        "\n"
        "    def for_window(self, names=None):\n"
        "        \"\"\"The requests of other devices' questions that wait for the PC window (1.0.17 item C): the window does them\n"
        "        and answers through /api/control-result, as it answers its own question's control.requested events.\"\"\"\n"
        "        names = names or {}\n"
        "        with self.lock:\n"
        "            return [{'id': ident, 'run_id': item['run'].id, 'action': item['action'], 'device': names.get(getattr(item['run'], 'device', ''), getattr(item['run'], 'device', ''))}\n"
        "                    for ident, item in self.pending.items() if getattr(item['run'], 'wearable', False) and not item['event'].is_set() and not item['run'].cancel.is_set()]\n"
        "\n"
        "    def request(self, action, run, timeout=None):\n"
        "        if action not in CONTROL_ACTIONS or run is None: raise ValueError('A connected conversation is required.')\n"
        "        if timeout is None: timeout = self.DEVICE_TIMEOUT if getattr(run, 'wearable', False) else 30\n",
    ),
    (
        "            if not isinstance(result, dict) or set(result)-{'status','active','error','sampling','image_submitted'}: raise ValueError('Invalid control result.')\n",
        "            if not isinstance(result, dict) or set(result)-{'status','active','error','sampling','image_submitted','attachment'}: raise ValueError('Invalid control result.')\n"
        "            if 'attachment' in result and not (isinstance(result['attachment'], str) and re.fullmatch(r'[a-f0-9]{32}', result['attachment'])): raise ValueError('Invalid control result.')\n",
    ),
])

# ---------------------------------------------------------------- items C and D: server.py (CRLF)
edit("server.py", [
    (
        "    def start_run(self, body, *, wearable=False, device=None, writes=False, tools=False):\n",
        "    def start_run(self, body, *, wearable=False, device=None, writes=False, tools=False, location=None):\n",
    ),
    (
        "            run.tools = tools    # a paired device the owner lets use this PC's tools (1.0.17); read again at every tool call\n",
        "            run.tools = tools    # a paired device the owner lets use this PC's tools (1.0.17); read again at every tool call\n"
        "            run.location = location  # the device's position sent with this question (1.0.17 item D): this answer only, kept nowhere\n",
    ),
    (
        "                context['recent_tool_evidence'] = self.store.recent_evidence(run.conversation)\n",
        "                context['recent_tool_evidence'] = self.store.recent_evidence(run.conversation)\n"
        "                if getattr(run, 'location', None):\n"
        "                    # 1.0.17 item D: the device's position, for this answer only; the Core keeps it nowhere and never shows it in a reply unasked.\n"
        "                    context['device_location'] = {**run.location, 'note': 'Reported by the device with this question; current, not stored, not tracked. Use it for directions, nearby places and local time; never claim to track the owner.'}\n",
    ),
    (
        "            elif name == 'assistant_control':\n"
        "                result = self.controls.request(args['action'], run)\n",
        "            elif name == 'assistant_control':\n"
        "                result = self.controls.request(args['action'], run)\n"
        "                if run is not None and getattr(run, 'wearable', False):\n"
        "                    result = self.device_control_result(run, args['action'], result)  # 1.0.17 item C\n",
    ),
    (
        "            elif name == 'get_directions':\n"
        "                result = maps.directions(args['origin'], args['destination'], args['mode'])\n",
        "            elif name == 'get_directions':\n"
        "                result = maps.directions(args['origin'], args['destination'], args['mode'], location=getattr(run, 'location', None))\n",
    ),
    (
        "    def approvals_waiting(self):\n",
        "    def device_control_result(self, run, action, result):\n"
        "        \"\"\"A paired device's question asked the PC window for a control (1.0.17, docs/PHONE-ACCESS-1.0.17.md item C).\n"
        "        The window learns of it from /api/control-requests and answers through /api/control-result as it answers\n"
        "        its own question's requests; for \"analyse my screen\" it uploads one capture, and the Core describes that\n"
        "        picture here, for this answer only. No window: said plainly, nothing claimed.\"\"\"\n"
        "        if result.get('status') == 'unconfirmed':\n"
        "            return {'status': 'unavailable', 'action': action, 'error': \"The PC's window is not open, so this cannot be done from here.\"}\n"
        "        if action != 'analyse_screen' or result.get('status') != 'completed':\n"
        "            return result\n"
        "        with self.lock:\n"
        "            attachment = self.attachments.pop(result.get('attachment') or '', None)\n"
        "        if not attachment or attachment.get('type') != 'image':\n"
        "            return {'status': 'failed', 'action': action, 'error': 'The PC window sent no capture.'}\n"
        "        description = self.describe_picture(run, attachment, \"Describe what is on the PC's screen right now for the owner, who asked from another device: \"\n"
        "                                            'what is open, the main text, and anything that needs attention. Say only what is visible.')\n"
        "        return {'status': 'completed', 'action': action, 'source': \"one capture of the PC's screen, not kept\", 'captured_at': result.get('checked_at'), 'description': description}\n"
        "\n"
        "    def describe_picture(self, run, attachment, question):\n"
        "        \"\"\"One model request with a picture and no tools; its words and nothing else (1.0.17 item C).\"\"\"\n"
        "        if not (os.getenv('OPENAI_API_KEY') or os.getenv('DASHSCOPE_API_KEY')):\n"
        "            raise ValueError('Image analysis needs a configured vision model.')\n"
        "        messages = [{'role': 'system', 'content': self.instructions(wearable=True)},\n"
        "                    {'role': 'user', 'content': [{'type': 'text', 'text': question}, {'type': 'image_url', 'image_url': {'url': attachment['data']}}]}]\n"
        "        depth = providers.chat_options(self.store.settings().get('answer_mode'), question)\n"
        "        response = providers.chat(messages, [], lambda *_: None, run.cancel, True, **depth)\n"
        "        return str((response or {}).get('content') or '')\n"
        "\n"
        "    def approvals_waiting(self):\n",
    ),
    (
        "            if path == '/api/devices':\n"
        "                return self.send(200, self.app.devices_listing())\n",
        "            if path == '/api/devices':\n"
        "                return self.send(200, self.app.devices_listing())\n"
        "            if path == '/api/control-requests':\n"
        "                # 1.0.17 item C: what other devices' questions ask this window to do (the signed-in interface only).\n"
        "                names = self.app.device_book.names() if self.app.device_book else {}\n"
        "                return self.send(200, {'requests': self.app.controls.for_window(names)})\n",
    ),
])

# ---------------------------------------------------------------- item C: static/app.js (mixed endings: byte edit)
edit_bytes("static/app.js", [
    (
        "setInterval(()=>{if(!document.hidden&&!state.busy)refresh();},10000);\n",
        "setInterval(()=>{if(!document.hidden&&!state.busy)refresh();},10000);\n"
        "// 1.0.17 item C (docs/PHONE-ACCESS-1.0.17.md): a paired device's question may ask this window for a control (\"analyse my\n"
        "// screen\" from the phone). The Core lists it at /api/control-requests; this window does it and answers through\n"
        "// /api/control-result, as it answers its own question's control.requested events. A capture is uploaded and handed to\n"
        "// the Core by its id; the Core describes it. Nothing is captured unless a display is already authorised here.\n"
        "const deviceControlsSeen=new Set();\n"
        "async function deviceControl(req){\n"
        " deviceControlsSeen.add(req.id);\n"
        " let result;\n"
        " try{\n"
        "  if(req.action==='analyse_screen'){\n"
        "   if(screenCaptureBusy||screenSending||state.busy)result={status:'failed',error:'The PC window is busy.'};\n"
        "   else if(window.jarvisDesktop&&!desktopLive&&!desktopScreen)result={status:'unavailable',error:'No display is authorised on the PC. Open JARVIS there, Communications > Screen Vision, and authorise a display.'};\n"
        "   else{\n"
        "    if(window.jarvisDesktop&&!desktopLive)await captureDesktopScreen(false,'');else await captureSharedScreen(false);\n"
        "    if(!screenBlob)result={status:'unavailable',error:'No screen is shared or authorised on the PC.'};\n"
        "    else{const attachment=await api('/api/upload',{name:'screen-capture.jpg',data:await blobBase64(screenBlob)});result={status:'completed',image_submitted:true,attachment:attachment.id};if(window.jarvisDesktop)discardScreenPreview();}\n"
        "   }\n"
        "  }else result=await performAssistantControl(req.action);\n"
        " }catch(e){result={status:'failed',error:'The requested control failed; no success confirmed.'};}\n"
        " try{await api('/api/control-result',{id:req.id,run_id:req.run_id,result});}catch{}\n"
        "}\n"
        "setInterval(async()=>{if(window.JARVIS_INSPECTION||!state.connected)return;try{const r=await api('/api/control-requests');for(const req of r.requests||[])if(!deviceControlsSeen.has(req.id))void deviceControl(req);}catch{}},3000);\n",
    ),
])
print("items C and D edits applied")
