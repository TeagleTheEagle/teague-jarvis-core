from pathlib import Path
root=Path(__file__).resolve().parent/'candidate'
p=root/'static/app.js';s=p.read_text(encoding='utf-8');marker='// Exact local controls bypass model latency'
before,fragment=s.split(marker,1)
(root/'static/assistant-controls.js').write_text(marker+fragment,encoding='utf-8')
p.write_text(before,encoding='utf-8')
p=root/'static/index.html';s=p.read_text(encoding='utf-8').replace('<script src="/app.js" defer></script>','<script src="/app.js" defer></script><script src="/assistant-controls.js" defer></script>');p.write_text(s,encoding='utf-8')
p=root/'server.py';s=p.read_text(encoding='utf-8').replace("mapping = {'/desktop-updates.js'", "mapping = {'/assistant-controls.js':'assistant-controls.js', '/desktop-updates.js'");p.write_text(s,encoding='utf-8')
p=root/'inspection_runtime.py';s=p.read_text(encoding='utf-8').replace("'inspection-client.js','desktop-updates.js')", "'inspection-client.js','desktop-updates.js','assistant-controls.js')");p.write_text(s,encoding='utf-8')
# Fix the existing cancellation test's checkout-specific path for isolated runs.
p=root/'test_voice_cancellation.cjs';s=p.read_text(encoding='utf-8').replace("fs.readFileSync('outputs/jarvis/static/app.js','utf8')","fs.readFileSync(__dirname+'/static/app.js','utf8')");p.write_text(s,encoding='utf-8')
