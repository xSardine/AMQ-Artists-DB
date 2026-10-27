"""SQLite schema, transactions, and queries for contribution history."""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS targets (
 id TEXT PRIMARY KEY, lookup_key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,
 locator_json TEXT NOT NULL, identity_snapshot_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS submissions (
 id INTEGER PRIMARY KEY, contributor_name TEXT NOT NULL, comment TEXT NOT NULL,
 submitted_at TEXT NOT NULL, client_request_id TEXT NOT NULL UNIQUE, payload_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS changes (
 id INTEGER PRIMARY KEY, submission_id INTEGER NOT NULL REFERENCES submissions(id),
 target_id TEXT NOT NULL REFERENCES targets(id), field TEXT NOT NULL, operation TEXT NOT NULL,
 before_value_json TEXT NOT NULL, proposed_value_json TEXT NOT NULL,
 submitted_base_revision INTEGER NOT NULL, review_status TEXT NOT NULL DEFAULT 'pending',
 review_version INTEGER NOT NULL DEFAULT 0, position INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS review_events (
 id INTEGER PRIMARY KEY, change_id INTEGER NOT NULL REFERENCES changes(id),
 reviewer_name TEXT NOT NULL, action TEXT NOT NULL, reviewed_value_json TEXT,
 comment TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approved_revisions (
 revision INTEGER PRIMARY KEY AUTOINCREMENT, change_id INTEGER NOT NULL REFERENCES changes(id),
 review_event_id INTEGER NOT NULL REFERENCES review_events(id), target_id TEXT NOT NULL REFERENCES targets(id),
 field TEXT NOT NULL, operation TEXT NOT NULL, approved_value_json TEXT NOT NULL,
 previous_field_revision INTEGER NOT NULL, reverts_revision INTEGER REFERENCES approved_revisions(revision),
 approved_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS catalog_loads (
 id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, completed_at TEXT,
 imported_catalog_fingerprint TEXT NOT NULL, contribution_revision_loaded INTEGER NOT NULL,
 success INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS catalog_load_issues (
 id INTEGER PRIMARY KEY, catalog_load_id INTEGER NOT NULL REFERENCES catalog_loads(id),
 approved_revision INTEGER NOT NULL REFERENCES approved_revisions(revision),
 target_id TEXT NOT NULL REFERENCES targets(id), reason TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS changes_submission ON changes(submission_id, position);
CREATE INDEX IF NOT EXISTS changes_status ON changes(review_status, submission_id);
CREATE INDEX IF NOT EXISTS revisions_field ON approved_revisions(target_id, field, revision);
CREATE INDEX IF NOT EXISTS events_change ON review_events(change_id, id);
"""


class ContributionStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.RLock()
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection(write=True) as transaction:
            transaction.create_schema()

    @contextmanager
    def connection(self, write: bool = False):
        with self.lock:
            connection = sqlite3.connect(self.path, timeout=15)
            connection.row_factory = sqlite3.Row
            connection.execute('PRAGMA foreign_keys=ON')
            if not write:
                connection.execute('PRAGMA query_only=ON')
            try:
                connection.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
                yield ContributionTransaction(connection)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()


class ContributionTransaction:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create_schema(self):
        for statement in SCHEMA.split(";"):
            if statement.strip():
                self.connection.execute(statement)

    def artist_targets(self):
        return self.connection.execute("SELECT * FROM targets WHERE kind='artist'").fetchall()

    def complete_load(self, completed_at, load_id):
        self.connection.execute(
            'UPDATE catalog_loads SET success=1,completed_at=? WHERE id=?',
            (completed_at, load_id),
        )

    def insert_target(self, target_id, lookup_key, kind, locator_json, identity_json, created_at):
        self.connection.execute(
            'INSERT INTO targets VALUES(?,?,?,?,?,?)',
            (target_id, lookup_key, kind, locator_json, identity_json, created_at),
        )

    def field_revisions(self, target_id, field):
        return self.connection.execute(
            'SELECT * FROM approved_revisions WHERE target_id=? AND field=? ORDER BY revision',
            (target_id, field),
        ).fetchall()

    def revisions_for_fields(self, fields):
        placeholders = ",".join("?" for _ in fields)
        return self.connection.execute(
            f'SELECT * FROM approved_revisions WHERE field IN ({placeholders}) ORDER BY revision',
            fields,
        ).fetchall()

    def review_events(self, change_id, limit, offset):
        return self.connection.execute(
            'SELECT * FROM review_events WHERE change_id=? ORDER BY id DESC LIMIT ? OFFSET ?',
            (change_id, limit, offset),
        ).fetchall()

    def load_issues(self, load_id, limit, offset):
        return self.connection.execute(
            'SELECT i.*,t.identity_snapshot_json FROM catalog_load_issues i JOIN targets t ON '
            't.id=i.target_id WHERE catalog_load_id=? ORDER BY i.id LIMIT ? OFFSET ?',
            (load_id, limit, offset),
        ).fetchall()

    def insert_revert(
        self,
        change_id,
        event_id,
        target_id,
        field,
        operation,
        payload,
        parent,
        reverts,
        created_at,
    ):
        self.connection.execute(
            'INSERT INTO approved_revisions(change_id,review_event_id,target_id,field,operation,'
            'approved_value_json,previous_field_revision,reverts_revision,approved_at) VALUES(?,'
            '?,?,?,?,?,?,?,?)',
            (change_id, event_id, target_id, field, operation, payload, parent, reverts, created_at),
        )

    def update_change(self, status, change_id):
        self.connection.execute(
            'UPDATE changes SET review_status=?,review_version=review_version+1 WHERE id=?',
            (status, change_id),
        )

    def all_revisions(self):
        return self.connection.execute('SELECT * FROM approved_revisions ORDER BY revision').fetchall()

    def insert_load(self, started_at, fingerprint, loaded_revision):
        return self.connection.execute(
            'INSERT INTO catalog_loads(started_at,imported_catalog_fingerprint,'
            'contribution_revision_loaded) VALUES(?,?,?)',
            (started_at, fingerprint, loaded_revision),
        ).lastrowid

    def insert_submission(self, name, comment, created_at, request_id, digest):
        return self.connection.execute(
            'INSERT INTO submissions(contributor_name,comment,submitted_at,client_request_id,'
            'payload_hash) VALUES(?,?,?,?,?)',
            (name, comment, created_at, request_id, digest),
        ).lastrowid

    def insert_change(
        self,
        submission_id,
        target_id,
        field,
        operation,
        before_json,
        proposed_json,
        base_revision,
        position,
    ):
        self.connection.execute(
            'INSERT INTO changes(submission_id,target_id,field,operation,before_value_json,'
            'proposed_value_json,submitted_base_revision,position) VALUES(?,?,?,?,?,?,?,?)',
            (
                submission_id,
                target_id,
                field,
                operation,
                before_json,
                proposed_json,
                base_revision,
                position,
            ),
        )

    def status_counts(self):
        return self.connection.execute('SELECT review_status,count(*) FROM changes GROUP BY review_status').fetchall()

    def submission_changes(self, submission_id):
        return self.connection.execute(
            'SELECT c.*, (SELECT count(*) FROM review_events e WHERE e.change_id=c.id) AS '
            'event_count, (SELECT reviewed_value_json FROM review_events e WHERE '
            'e.change_id=c.id AND reviewed_value_json IS NOT NULL ORDER BY e.id DESC LIMIT 1) '
            'AS last_reviewed_value_json FROM changes c WHERE submission_id=? ORDER BY position',
            (submission_id,),
        ).fetchall()

    def revisions_for_targets(self, target_ids):
        placeholders = ",".join("?" for _ in target_ids)
        return self.connection.execute(
            f'SELECT * FROM approved_revisions WHERE target_id IN ({placeholders}) ORDER BY '
            f'revision',
            target_ids,
        ).fetchall()

    def insert_undo_event(self, change_id, name, action, comment, created_at):
        return self.connection.execute(
            'INSERT INTO review_events(change_id,reviewer_name,action,comment,created_at) '
            'VALUES(?,?,?,?,?)',
            (change_id, name, action, comment, created_at),
        ).lastrowid

    def all_targets(self):
        return self.connection.execute('SELECT * FROM targets').fetchall()

    def target(self, target_id):
        return self.connection.execute('SELECT * FROM targets WHERE id=?', (target_id,)).fetchone()

    def submission_by_request(self, request_id):
        return self.connection.execute(
            'SELECT * FROM submissions WHERE client_request_id=?',
            (request_id,),
        ).fetchone()

    def submission(self, submission_id):
        return self.connection.execute('SELECT * FROM submissions WHERE id=?', (submission_id,)).fetchone()

    def targets_by_ids(self, target_ids):
        placeholders = ",".join("?" for _ in target_ids)
        return self.connection.execute(f'SELECT * FROM targets WHERE id IN ({placeholders})', target_ids).fetchall()

    def insert_review_event(self, change_id, name, action, payload, comment, created_at):
        return self.connection.execute(
            'INSERT INTO review_events(change_id,reviewer_name,action,reviewed_value_json,'
            'comment,created_at) VALUES(?,?,?,?,?,?)',
            (change_id, name, action, payload, comment, created_at),
        ).lastrowid

    def insert_revision(
        self,
        change_id,
        event_id,
        target_id,
        field,
        operation,
        payload,
        parent,
        created_at,
    ):
        return self.connection.execute(
            'INSERT INTO approved_revisions(change_id,review_event_id,target_id,field,operation,'
            'approved_value_json,previous_field_revision,approved_at) VALUES(?,?,?,?,?,?,?,?)',
            (change_id, event_id, target_id, field, operation, payload, parent, created_at),
        ).lastrowid

    def revision(self, revision, target_id, field):
        return self.connection.execute(
            'SELECT * FROM approved_revisions WHERE revision=? AND target_id=? AND field=?',
            (revision, target_id, field),
        ).fetchone()

    def insert_load_issue(self, load_id, revision, target_id, reason):
        self.connection.execute(
            'INSERT INTO catalog_load_issues(catalog_load_id,approved_revision,target_id,'
            'reason) VALUES(?,?,?,?)',
            (load_id, revision, target_id, reason),
        )

    def latest_revision(self):
        return self.connection.execute('SELECT coalesce(max(revision),0) FROM approved_revisions').fetchone()[0]

    def waiting_fields(self, loaded_revision):
        return self.connection.execute(
            'SELECT count(*) FROM (SELECT target_id,field FROM approved_revisions WHERE '
            'revision>? GROUP BY target_id,field)',
            (loaded_revision,),
        ).fetchone()[0]

    def issue_count(self, load_id):
        return self.connection.execute(
            'SELECT count(*) FROM catalog_load_issues WHERE catalog_load_id=?',
            (load_id,),
        ).fetchone()[0]

    def change(self, change_id):
        return self.connection.execute('SELECT * FROM changes WHERE id=?', (change_id,)).fetchone()

    def history_count(self, change_id):
        return self.connection.execute(
            'SELECT count(*) FROM review_events WHERE change_id=?',
            (change_id,),
        ).fetchone()[0]

    def submissions(self, status, before, limit, kind=None, search=""):
        filters, args = ([], [before])
        if status != 'all':
            filters.append('c.review_status=?')
            args.append(status)
        if kind:
            filters.append('t.kind=?')
            args.append(kind)
        condition = ''
        if filters:
            condition += ' AND EXISTS(SELECT 1 FROM changes c JOIN targets t ON t.id=c.target_id WHERE c.submission_id=s.id AND ' + ' AND '.join(filters) + ')'
        if search.strip():
            condition += " AND (s.contributor_name LIKE ? ESCAPE '\\' OR s.comment LIKE ? ESCAPE '\\' OR cast(s.id AS TEXT) LIKE ? ESCAPE '\\' OR EXISTS(SELECT 1 FROM changes c JOIN targets t ON t.id=c.target_id WHERE c.submission_id=s.id AND t.identity_snapshot_json LIKE ? ESCAPE '\\'))"
            term = '%' + search.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
            args.extend([term] * 4)
        args.append(limit + 1)
        rows = list(self.connection.execute(
            f'SELECT s.*, (SELECT count(*) FROM changes c WHERE c.submission_id=s.id) AS '
            f'change_count FROM submissions s WHERE s.id<?{condition} ORDER BY s.id DESC LIMIT ?',
            args,
        ))
        return rows

    def version(self, target_id, field, boundary=None):
        sql = (
            "SELECT coalesce(max(revision),0) FROM approved_revisions WHERE target_id=? AND field=?"
        )
        args = [target_id, field]
        if boundary is not None:
            sql += " AND revision<=?"
            args.append(boundary)
        return self.connection.execute(sql, args).fetchone()[0]
