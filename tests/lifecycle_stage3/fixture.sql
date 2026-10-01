-- TEST ONLY: frozen schema from read-only AST inspection, not production imports.

                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL,
                    created REAL NOT NULL, updated REAL NOT NULL,
                    item_key TEXT, category TEXT, source TEXT, confidence REAL NOT NULL DEFAULT 1.0);
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, conversation TEXT NOT NULL,
                    role TEXT NOT NULL, content TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, due REAL NOT NULL,
                    fired INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL,
                    status TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, conversation TEXT, message TEXT,
                    rating TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, content TEXT NOT NULL,
                    created REAL NOT NULL, updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS task_meta (
                    item_id TEXT PRIMARY KEY, priority TEXT NOT NULL DEFAULT 'normal',
                    due REAL, recurrence TEXT, completed INTEGER NOT NULL DEFAULT 0,
                    completed_at REAL);
                CREATE TABLE IF NOT EXISTS research (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, conversation TEXT NOT NULL,
                    query TEXT NOT NULL, result TEXT NOT NULL, created REAL NOT NULL);
                PRAGMA user_version=1;
                CREATE TABLE IF NOT EXISTS turn_evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, conversation TEXT NOT NULL,
                    tool TEXT NOT NULL, result TEXT NOT NULL, created REAL NOT NULL);

CREATE TABLE IF NOT EXISTS workspaces(id TEXT PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS workspace_links(project TEXT, kind TEXT, ref TEXT, title TEXT, content TEXT,
        PRIMARY KEY(project,kind,ref));

        CREATE TABLE IF NOT EXISTS project_budget_limits (
            project TEXT PRIMARY KEY, core_requests INTEGER NOT NULL,
            container_checks INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS project_budget_reservations (
            project TEXT NOT NULL, operation TEXT NOT NULL, task TEXT NOT NULL,
            core_requests INTEGER NOT NULL, container_checks INTEGER NOT NULL,
            created REAL NOT NULL, PRIMARY KEY(project, operation));

ALTER TABLE project_budget_reservations ADD COLUMN state TEXT NOT NULL DEFAULT 'recovery_required';
ALTER TABLE project_budget_reservations ADD COLUMN started INTEGER NOT NULL DEFAULT 1;
ALTER TABLE project_budget_reservations ADD COLUMN used_core INTEGER NOT NULL DEFAULT 0;
ALTER TABLE project_budget_reservations ADD COLUMN used_container INTEGER NOT NULL DEFAULT 0;
ALTER TABLE project_budget_reservations ADD COLUMN expires REAL NOT NULL DEFAULT 0;
ALTER TABLE project_budget_reservations ADD COLUMN revision INTEGER NOT NULL DEFAULT 0;
ALTER TABLE project_budget_reservations ADD COLUMN outcome TEXT NOT NULL DEFAULT '';
ALTER TABLE project_budget_reservations ADD COLUMN evidence TEXT NOT NULL DEFAULT '';
