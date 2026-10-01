from pathlib import Path
root=Path(__file__).resolve().parent/'candidate'
p=root/'static/inspection-client.js';s=p.read_text(encoding='utf-8')
s=s.replace('Captures expire after five minutes. Reports are not saved automatically.','Captures expire after five minutes and are not archived. Completed, partial and failed reports are saved locally in Project Jarvis; archive success is shown separately.')
s=s.replace("job.current_panel?'Capturing and analysing '+job.current_panel:'Consolidating findings'", "job.phase==='archiving'?'Saving inspection report':job.current_panel?'Capturing and analysing '+job.current_panel:'Consolidating findings'")
p.write_text(s,encoding='utf-8')
