"""Prepare a review-only server candidate; never replace the installed server."""
from pathlib import Path
import ast
import difflib
import development

root = Path(__file__).resolve().parents[1]
source = (root / 'server.py').read_text(encoding='utf-8')
start = source.index("            elif name == 'daily_briefing':")
end = source.index("            elif name == 'image_search':", start)
replacement = '''            elif name == 'daily_briefing':
                result = {'checks': {}, 'generated_at': time.time()}
                sources = {
                    'news': (lambda: actions.news_search('top news'), 5),
                    'tasks': (lambda: self.store.tasks(include_completed=False), 8),
                    'projects': (lambda: workspaces.listing(self.store), 6),
                    'reminders': (self.store.reminders, 8),
                }
                for section, (check, limit) in sources.items():
                    started = time.perf_counter()
                    try:
                        payload = check()
                        rows = payload['results'] if section == 'news' else payload
                        if not isinstance(rows, list):
                            raise ValueError('Invalid briefing source')
                        result[section] = rows[:limit]
                        result['checks'][section] = {
                            'status': 'ok' if rows else 'empty',
                            'checked_at': time.time(), 'total': len(rows),
                            'truncated': len(rows) > limit,
                        }
                        if section == 'news':
                            result['checks'][section]['retrieved_at'] = payload.get('retrieved_at')
                    except Exception:
                        result[section] = []
                        result['checks'][section] = {
                            'status': 'unavailable', 'checked_at': time.time(),
                            'message': 'Could not check this source. Do not infer that nothing exists.',
                        }
                    result['checks'][section]['duration_ms'] = round((time.perf_counter() - started) * 1000, 2)
                result['evidence_rule'] = 'Use checks for availability. Retrieval time is not publication time. Unknown publication dates are not verified current news. Truncated lists are partial.'
'''
candidate = source[:start] + replacement + source[end:]
ast.parse(candidate)
(root / 'review/server_candidate.py').write_text(candidate, encoding='utf-8')
(root / 'review/briefing.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True), candidate.splitlines(True), fromfile='server.py', tofile='server.py')), encoding='utf-8')

# Personality is an explicitly authorised immediate-change target. Preserve its
# backup and diff using the existing development mechanism.
before = development.read(root, 'personality.txt')
after = before.replace('Treat headlines as current information and do not invent details beyond the feed.', 'Check publication dates before describing headlines as current; retrieval time alone does not prove publication freshness. Label old or undated items and do not invent details beyond the feed.')
addition = '''
Briefing evidence rules: make a fresh daily_briefing call for every new briefing request; earlier conversation and stored tool evidence are historical context, not current status. Verify Projects using project_catalog because the legacy briefing project list may differ from the Projects workspace. If daily_briefing fails, report that it could not be checked; use available list_items and project_catalog checks for partial information, but do not claim reminders were checked if no reminder result was returned. Say "nothing found" only after a successful empty check. When checks metadata is present, unavailable means could not check, empty means successfully checked with no results, and truncated means partial. Use news_search if fresh news retrieval metadata is missing. Preserve the distinction between publication time, retrieval time and the time the briefing was assembled.
Action evidence rules: distinguish proposed, awaiting approval, cancelled, failed, scheduled and completed. A submitted request or navigation request is not proof of completion or rendering. Use the actual tool result before confirming a saved item or scheduled timer. Do not repeat a successful write to answer a follow-up. For ambiguous "save that", ask which content to save before creating anything. Keep temporary conversation context separate from explicitly saved memory. Never describe the microphone as listening or claim a measured latency without supporting diagnostics. If measurements are unavailable, say they were not measured.
'''
if 'Briefing evidence rules:' not in after:
    after += addition
if after != before:
    proposal = development.prepare(root, 'personality.txt', after, 'Require fresh briefing evidence, accurate action states and clarification of ambiguous saves.')
    development.apply(root, proposal['proposal'])
    (root / 'review/personality_proposal.txt').write_text(proposal['proposal'], encoding='utf-8')
    print('Applied personality proposal:', proposal['proposal'])
print('Server candidate and diff prepared only; installed server unchanged.')
