"""Bounded inspection request/evidence contract used by the app and tools."""
from panel_registry import WORKSPACE_PANELS as PANELS
SCOPES = ('viewport', 'full_panel')
STAGES = ('navigation_requested', 'panel_rendered', 'screenshot_captured',
          'image_submitted', 'analysis_completed')


def validate_request(arguments):
    if not isinstance(arguments, dict) or set(arguments) - {'panel', 'scope', 'focus'}:
        raise ValueError('Only panel, scope and focus are accepted.')
    panel = arguments.get('panel')
    scope = arguments.get('scope', 'full_panel' if panel == 'all' else 'viewport')
    focus = arguments.get('focus', '')
    if not isinstance(panel, str) or panel not in (*PANELS, 'all'):
        raise ValueError('Unsupported JARVIS panel.')
    if not isinstance(scope, str) or scope not in SCOPES:
        raise ValueError('Unsupported capture scope.')
    if not isinstance(focus, str) or len(focus) > 2000:
        raise ValueError('Focus must be text of at most 2000 characters.')
    return {'panel': panel, 'scope': scope, 'focus': focus.strip()}


def new_evidence(arguments):
    request = validate_request(arguments)
    return {
        'requested_panel': request['panel'], 'verified_panel': None,
        'requested_scope': request['scope'], 'captured_at': None,
        'viewport': None, 'coverage': 'none', 'omissions': [],
        'visible_text': '', 'accessibility': [], 'screenshots': [],
        'stages': {stage: 'not_attempted' for stage in STAGES},
        'assessment_mode': 'none', 'provider': None,
        'errors': [], 'limitations': [],
    }


def tool_schema():
    return {'type': 'function', 'function': {
        'name': 'inspect_interface',
        'description': 'On an explicit inspection request, use panel="all" to inspect the whole interface in ONE job, or name one panel. Whole-interface inspection is supported. Captures run sequentially, then produce a consolidated review. '
                       'Does not navigate the visible interface or apply fixes. '
                       'Report actual capture and analysis status.',
        'parameters': {'type': 'object', 'additionalProperties': False,
            'required': ['panel'], 'properties': {
                'panel': {'type': 'string', 'enum': [*PANELS, 'all']},
                'scope': {'type': 'string', 'enum': list(SCOPES)},
                'focus': {'type': 'string', 'maxLength': 2000}}}}}
