from pathlib import Path
root=Path(__file__).resolve().parent/'candidate'
p=root/'static/app.js'
s=p.read_text(encoding='utf-8')
s=s.replace('if(state.busy||screenSending){toast(', 'if((state.busy&&!options.fromAssistant)||screenSending){toast(')
s=s.replace("if(event.event==='run.cancelled'){output", "if(event.event==='run.cancelled'){state.interrupted=true;output")
s=s.replace("if(event.event==='run.failed'){if", "if(event.event==='run.failed'){state.interrupted=true;if")
p.write_text(s,encoding='utf-8')
