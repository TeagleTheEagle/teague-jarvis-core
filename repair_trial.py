"""Review-only real-Core trial. Generated Python is parsed, NEVER executed.

The evaluator supports only delay(seconds) returning numeric min/max expressions.
It is not a sandbox for general Python. No App, Store or provider is instantiated.
"""
import ast
import asyncio
import hashlib
import json
import math
from pathlib import Path
import tempfile
import time
import uuid

import development
from wearables.real_core import RealCore

BEFORE = 'def delay(seconds):\n    return seconds\n'
CASES = ((-5, 0), (0, 0), (2, 2), (.5, .5), (-.25, 0), (100, 100))
PROMPT = '''This is a review-only programming exercise in a disposable test copy.
Do not use tools, browse, read projects or modify any files. Return ONLY a Python
function, optionally in one python code fence. Diagnose and fix this faulty function:
def delay(seconds):
    return seconds
Requirement: negative numeric delays become zero; zero and positive numeric delays
are preserved, including fractions. Observed failure: delay(-5) returns -5.
Allowed syntax: exactly def delay(seconds) with one return; its expression may use
seconds, bounded numeric literals, unary minus, and min/max with two arguments.
No imports, annotations, defaults, decorators, other statements, tools or prose.
'''


def validate_candidate(source):
    if not isinstance(source, str) or len(source) > 2000:
        raise ValueError('Candidate exceeds limit.')
    tree = ast.parse(source)
    if len(list(ast.walk(tree))) > 40 or len(tree.body) != 1:
        raise ValueError('Candidate structure rejected.')
    fn = tree.body[0]
    if not isinstance(fn, ast.FunctionDef) or fn.name != 'delay':
        raise ValueError('Expected delay function.')
    a = fn.args
    if (fn.decorator_list or fn.returns or getattr(fn, 'type_params', []) or
        a.posonlyargs or a.vararg or a.kwarg or a.kwonlyargs or a.defaults or
        len(a.args) != 1 or a.args[0].arg != 'seconds' or a.args[0].annotation or
        len(fn.body) != 1 or not isinstance(fn.body[0], ast.Return)):
        raise ValueError('Function signature or statements rejected.')
    expression = fn.body[0].value
    def check(node):
        if isinstance(node, ast.Name) and node.id == 'seconds':
            return
        if isinstance(node, ast.Constant) and type(node.value) in (int, float) and math.isfinite(node.value) and abs(node.value) <= 1000000:
            return
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            check(node.operand)
            return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('min', 'max') and len(node.args) == 2 and not node.keywords:
            for arg in node.args:
                check(arg)
            return
        raise ValueError('Expression outside numeric subset.')
    check(expression)
    return expression


def evaluate(node, seconds):
    # Called only after validating the whole tree. No eval/exec/compile/import.
    if isinstance(node, ast.Name):
        return seconds
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp):
        return -evaluate(node.operand, seconds)
    values = [evaluate(arg, seconds) for arg in node.args]
    return min(values) if node.func.id == 'min' else max(values)


def score(source):
    expression = validate_candidate(source)
    return [evaluate(expression, value) == expected for value, expected in CASES]


def extract(answer):
    answer = answer.strip()
    if answer.startswith('```python\n') and answer.endswith('```'):
        answer = answer[len('```python\n'):-3].strip()
    return answer + '\n'


async def trial(core):
    started = time.monotonic()
    baseline = score(BEFORE)
    # Existing read-limited same-PC client: credentials remain in Core.
    answer = await asyncio.wait_for(core.respond(PROMPT, conversation='wearable-repair-trial-'+uuid.uuid4().hex[:12]), timeout=140)
    candidate = extract(answer)
    checks = score(candidate)  # Fail closed before staging any model text.
    with tempfile.TemporaryDirectory(prefix='jarvis-repair-trial-') as folder:
        root = Path(folder)
        (root/'wake.py').write_text(BEFORE, encoding='utf-8')
        proposal = development.prepare(root, 'wake.py', candidate, 'TEST ONLY: generated numeric delay repair')
        unchanged = (root/'wake.py').read_text(encoding='utf-8') == BEFORE
        return {'status': 'READY_FOR_REVIEW' if all(checks) and unchanged else 'FAILED',
                'test_only': True, 'core': 'existing running JARVIS via same-PC client',
                'baseline_passed': sum(baseline), 'candidate_passed': sum(checks), 'total': len(CASES),
                'candidate': candidate, 'diff': proposal['diff'], 'source_unchanged': unchanged,
                'candidate_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
                'evaluation': 'restricted numeric AST interpreter; generated Python never executed',
                'core_requests': 1, 'measurements': core.measurements,
                'elapsed_seconds': round(time.monotonic()-started, 3), 'deployed': False}


if __name__ == '__main__':
    try:
        report = asyncio.run(trial(RealCore()))
    except Exception as exc:
        # Do not expose raw provider/network exceptions or returned model text.
        report = {'status': 'FAILED', 'error_type': type(exc).__name__, 'deployed': False}
    path = Path(__file__).parent/'docs'/'repair-trial-result.json'
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'READY_FOR_REVIEW' else 1)
