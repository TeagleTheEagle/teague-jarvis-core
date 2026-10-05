"""Writes the fixed part of a JARVIS AI request, as server.py builds it, for tools/host/Test-AiKeys.ps1:
jarvis-request-system.txt (the default personality, tool guidance, verified-status guidance and development-tools
paragraph) and jarvis-request-tools.json (actions.TOOLS). With these the owner-run check can send a provider exactly
what JARVIS sends, tool list included, without touching the installed JARVIS. The owner's own personality.txt is not
read; the shipped default stands in for it.
    python tools/host/make_request_template.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import actions  # noqa: E402
import conversation_context  # noqa: E402
import verified_status  # noqa: E402


def development_paragraph():
    # The paragraph server.py appends after the guidance (one line in Handler/App code).
    source = (ROOT / 'server.py').read_text(encoding='utf-8')
    match = re.search(r"system \+= '\\nYou have real development_read.*?'\n", source)
    if not match:
        raise SystemExit('development paragraph not found in server.py')
    return eval(match.group(0).split('+=', 1)[1].strip())  # a plain string literal from our own source


def main():
    system = (ROOT / 'personality.txt').read_text(encoding='utf-8')
    system += '\n' + conversation_context.TOOL_GUIDANCE + '\n' + verified_status.GUIDANCE + development_paragraph()
    here = Path(__file__).resolve().parent
    (here / 'jarvis-request-system.txt').write_text(system, encoding='utf-8', newline='\n')
    (here / 'jarvis-request-tools.json').write_text(json.dumps(actions.TOOLS, ensure_ascii=False), encoding='utf-8', newline='\n')
    print(f'system {len(system)} characters, {len(actions.TOOLS)} tools ({len(json.dumps(actions.TOOLS))} characters)')


if __name__ == '__main__':
    main()
