"""Atomic resource reservations in the existing Core Store, not a new owner.

Reservations conservatively consume capacity before work. No automatic refunds,
provider calls, scheduler, deployment or monetary estimates are implemented here.
"""
import math
import time

RESOURCES = ('core_requests', 'container_checks')


def setup(db):
    db.executescript('''
        CREATE TABLE IF NOT EXISTS project_budget_limits (
            project TEXT PRIMARY KEY, core_requests INTEGER NOT NULL,
            container_checks INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS project_budget_reservations (
            project TEXT NOT NULL, operation TEXT NOT NULL, task TEXT NOT NULL,
            core_requests INTEGER NOT NULL, container_checks INTEGER NOT NULL,
            created REAL NOT NULL, PRIMARY KEY(project, operation));
    ''')
    columns = {r[1] for r in db.execute('PRAGMA table_info(project_budget_reservations)')}
    additions = {'state': "TEXT NOT NULL DEFAULT 'recovery_required'",
                 'started': 'INTEGER NOT NULL DEFAULT 1',
                 'used_core': 'INTEGER NOT NULL DEFAULT 0', 'used_container': 'INTEGER NOT NULL DEFAULT 0',
                 'expires': 'REAL NOT NULL DEFAULT 0', 'revision': 'INTEGER NOT NULL DEFAULT 0',
                 'outcome': "TEXT NOT NULL DEFAULT ''", 'evidence': "TEXT NOT NULL DEFAULT ''"}
    for column, definition in additions.items():
        if column not in columns:
            db.execute(f'ALTER TABLE project_budget_reservations ADD COLUMN {column} {definition}')


def amounts(value):
    if type(value) is not dict or set(value) != set(RESOURCES):
        raise ValueError('Specify core_requests and container_checks only.')
    if any(type(value[k]) is not int or not 0 <= value[k] <= 10000 for k in RESOURCES):
        raise ValueError('Resource counts must be integers from 0 to 10000.')
    return tuple(value[k] for k in RESOURCES)


def checked_rows(db, project):
    rows = [dict(r) for r in db.execute('SELECT * FROM project_budget_reservations WHERE project=?',(project,))]
    for row in rows:
        original = amounts({k:row[k] for k in RESOURCES})
        used = amounts(dict(core_requests=row['used_core'],container_checks=row['used_container']))
        if (row['state'] not in ('held','started','recovery_required','settled','released') or
                type(row['started']) is not int or row['started'] not in (0,1) or
                type(row['revision']) is not int or row['revision'] < 0 or
                any(used[i] > original[i] for i in range(2)) or
                any(type(row[k]) not in (int,float) or not math.isfinite(row[k]) for k in ('created','expires')) or
                (row['state']=='held' and row['started'] != 0) or
                (row['state']=='started' and row['started'] != 1) or
                (row['state']=='released' and (row['started'] or any(used))) or
                (row['state']=='settled' and (not row['started'] or row['outcome'] not in ('succeeded','failed') or not row['evidence']))):
            raise ValueError('Corrupted reservation; reconcile before further allocation.')
    return rows


def totals(db, project):
    result=[0,0]
    for row in checked_rows(db,project):
        charged = ((row['used_core'],row['used_container']) if row['state']=='settled' else
                   (0,0) if row['state']=='released' else tuple(row[k] for k in RESOURCES))
        for i in range(2): result[i] += charged[i]
    return tuple(result)


def snapshot(db, project):
    row = db.execute('SELECT core_requests,container_checks FROM project_budget_limits WHERE project=?', (project,)).fetchone()
    used = totals(db, project)
    if row:
        amounts(dict(zip(RESOURCES,row)))
        if any(used[i] > row[i] for i in range(2)):
            raise ValueError('Corrupted budget totals; reconcile before allocating.')
    reservations=checked_rows(db,project)
    consumed=tuple(sum(r[k] for r in reservations) for k in ('used_core','used_container'))
    return {'configured': row is not None, 'limits': dict(zip(RESOURCES,row)) if row else None,
            'reserved': dict(zip(RESOURCES,used)),
            'consumed': dict(zip(RESOURCES,consumed)),
            'held': dict(zip(RESOURCES,(used[i]-consumed[i] for i in range(2)))),
            'recovery_required': [r['operation'] for r in reservations if r['state']=='recovery_required' or
                                  (r['state'] in ('held','started') and time.time() >= r['expires'])],
            'remaining': dict(zip(RESOURCES,(row[i]-used[i] for i in range(2)))) if row else None,
            'cost_usd': None, 'execution_authorized': False}


def change(store, body):
    action = body.get('action')
    project = body.get('project')
    if type(project) is not str or not 1 <= len(project) <= 100:
        raise ValueError('Invalid project ID.')
    # One transaction locks competing reservations before reading their totals.
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM workspaces WHERE id=?',(project,)).fetchone():
            raise ValueError('Project not found.')
        if action == 'budget_configure':
            limits = amounts(body.get('limits'))
            used = totals(db,project)
            if any(limits[i] < used[i] for i in range(2)):
                raise ValueError('Limits cannot discard previous reservations.')
            db.execute('INSERT INTO project_budget_limits VALUES (?,?,?) ON CONFLICT(project) '
                       'DO UPDATE SET core_requests=excluded.core_requests,container_checks=excluded.container_checks',
                       (project,*limits))
            return snapshot(db,project)
        if action != 'budget_reserve':
            raise ValueError('Unknown budget action.')
        requested = amounts(body.get('resources'))
        if not any(requested): raise ValueError('Reserve at least one resource unit.')
        operation,task = body.get('operation'),body.get('task')
        if type(operation) is not str or not 1 <= len(operation) <= 100:
            raise ValueError('Use a stable operation ID for retries.')
        if type(task) is not str or not 1 <= len(task) <= 100:
            raise ValueError('Invalid task ID.')
        old=db.execute('SELECT task,core_requests,container_checks FROM project_budget_reservations '
                       'WHERE project=? AND operation=?',(project,operation)).fetchone()
        if old:
            if tuple(old) != (task,*requested): raise ValueError('Operation ID already has different inputs.')
            return {**snapshot(db,project),'operation':operation,'new_reservation':False,'replay':True}
        linked=db.execute("SELECT 1 FROM workspace_links l JOIN items i ON i.id=l.ref "
                          "WHERE l.project=? AND l.kind='task' AND l.ref=? AND i.kind='task'",(project,task)).fetchone()
        if not linked: raise ValueError('Reserve only for an existing task linked to this project.')
        budget=snapshot(db,project)
        if not budget['configured']: raise ValueError('Configure a project budget before reserving resources.')
        if any(requested[i] > budget['remaining'][key] for i,key in enumerate(RESOURCES)):
            raise ValueError('Project resource budget exhausted.')
        now=time.time()
        db.execute('INSERT INTO project_budget_reservations '
                   '(project,operation,task,core_requests,container_checks,created,state,started,expires) '
                   "VALUES (?,?,?,?,?,?,'held',0,?)",
                   (project,operation,task,*requested,now,now+300))
        return {**snapshot(db,project),'operation':operation,'new_reservation':True,'replay':False}


def lifecycle(store, project, operation, action, revision, usage=None, outcome='', evidence=''):
    """Internal trusted-Core hook. NOT exposed as a model tool or HTTP action.

Callers must verify execution outcome before settlement. Evidence is a reference
for audit, not an authorization token or proof inferred from candidate output.
"""
    if type(revision) is not int or revision < 0: raise ValueError('Expected revision required.')
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        rows=checked_rows(db,project)
        row=next((r for r in rows if r['operation']==operation),None)
        if row is None: raise ValueError('Reservation not found.')
        terminal=row['state'] in ('settled','released')
        used=amounts(usage) if usage is not None else (row['used_core'],row['used_container'])
        # Terminal retries are exact-match only; never return a fresh start grant.
        if terminal:
            same=(action=='release' and row['state']=='released') or (
                action=='settle' and row['state']=='settled' and
                used==(row['used_core'],row['used_container']) and outcome==row['outcome'] and evidence==row['evidence'])
            if not same: raise ValueError('Terminal reservation cannot change.')
            return {**row,'replay':True,'start_granted':False,'execution_authorized':False}
        if revision != row['revision']: raise ValueError('Stale reservation revision.')
        state=row['state']; started=row['started']
        if action=='uncertain':
            state='recovery_required'
        elif action=='expire':
            if time.time() < row['expires']: raise ValueError('Reservation has not expired.')
            state='recovery_required'
        elif action=='start':
            if state != 'held' or time.time() >= row['expires']:
                raise ValueError('Expired or previously started reservation; recovery required.')
            state='started'; started=1
        elif action=='release':
            if started or any(used): raise ValueError('Started work requires verified usage settlement.')
            state='released'
        elif action in ('consume','settle'):
            if not started or usage is None: raise ValueError('Started operation and measured usage required.')
            if any(used[i] < row[k] or used[i] > row[RESOURCES[i]] for i,k in enumerate(('used_core','used_container'))):
                raise ValueError('Consumption must be monotonic and within the reservation.')
            if action=='settle':
                if outcome not in ('succeeded','failed') or type(evidence) is not str or not 1<=len(evidence)<=200:
                    raise ValueError('Verified outcome and bounded evidence reference required.')
                state='settled'
        else: raise ValueError('Unknown lifecycle action.')
        db.execute('UPDATE project_budget_reservations SET state=?,started=?,used_core=?,used_container=?,revision=revision+1,outcome=?,evidence=? '
                   'WHERE project=? AND operation=?',
                   (state,started,*used,outcome if action=='settle' else row['outcome'],
                    evidence if action=='settle' else row['evidence'],project,operation))
        updated=dict(db.execute('SELECT * FROM project_budget_reservations WHERE project=? AND operation=?',(project,operation)).fetchone())
        return {**updated,'replay':False,'start_granted':action=='start','execution_authorized':False}
