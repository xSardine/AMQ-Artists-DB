"""Contribution workflows and catalog activation, independent of HTTP and SQL."""

import hashlib
import json
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from contribution.errors import (
    ContributionError,
    ContributionNotFound,
    ContributionConflict,
    InvalidContribution,
)
from contribution.store import ContributionStore
from contribution.rules import same_name, operate, effective
from contribution.targets import (
    artist_detail,
    song_type_label,
    describe,
    same_artist,
    resolve,
    field_values,
)

from contribution.models import (
    ALIASES,
    ARTIST_ID_FIELDS,
    FIELD_DEFINITIONS,
    FIELDS,
    ContributionPayload,
    validate_operation,
)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class ContributionService:
    def __init__(self, store: ContributionStore):
        self.store = store
        self.loaded_revision = 0
        self.load_id = None
        self.base_values = {}
        self._catalog = None
        self._candidates = {}


    def apply(self, songs, artists, fingerprint):
        """Called once during startup, before the final catalog indexes are built."""
        by_ann, by_song = defaultdict(list), defaultdict(list)
        for song in songs:
            by_ann[song.ann_id].append(song)
            by_song[song.ann_song_id].append(song)
        updated_songs, updated_artists = {}, dict(artists)
        with self.store.connection(write=True) as connection:
            targets = {row["id"]: row for row in connection.all_targets()}
            rows = list(connection.all_revisions())
            self.loaded_revision = rows[-1]["revision"] if rows else 0
            self.load_id = connection.insert_load(now(), fingerprint, self.loaded_revision)
            for target_id, target in targets.items():
                try:
                    values = field_values(target["kind"], resolve(target, by_ann, by_song, artists))
                    self.base_values.update(
                        {(target_id, field): value for field, value in values.items()}
                    )
                except ValueError:
                    pass
            for row in effective(rows):
                target = targets[row["target_id"]]
                try:
                    resolved = resolve(target, by_ann, by_song, artists)
                    attribute = FIELDS[target["kind"]][row["field"]]
                    payload = json.loads(row["approved_value_json"])
                    if target["kind"] == "artist":
                        artist_id = json.loads(target["locator_json"])["artist_id"]
                        current = updated_artists[artist_id]
                        value = operate(getattr(current, attribute), row["operation"], payload)
                        updated_artists[artist_id] = replace(
                            current,
                            **{attribute: tuple(value) if row["field"] in ALIASES else value},
                        )
                    else:
                        for source in resolved:
                            current = updated_songs.get(source.song_id, source)
                            value = operate(getattr(current, attribute), row["operation"], payload)
                            updated_songs[source.song_id] = replace(
                                current,
                                **{attribute: tuple(value) if row["field"] in ALIASES else value},
                            )
                except (ValueError, KeyError) as error:
                    connection.insert_load_issue(
                        self.load_id,
                        row['revision'],
                        target['id'],
                        str(error),
                    )
            return tuple(updated_songs.get(song.song_id, song) for song in songs), updated_artists

    def complete_load(self):
        with self.store.connection(write=True) as connection:
            connection.complete_load(now(), self.load_id)

    def _index_targets(self, catalog, connection):
        if self._catalog is catalog:
            return
        self._registered = {row['lookup_key']: row for row in connection.all_targets()}
        candidates = {}
        records = [
            ('anime', entry.songs[0]) for entry in catalog.anime_by_id.values()
        ]
        records.extend(('artist', item) for item in catalog.artists_by_id.items())
        records.extend(('song', song) for song in catalog.song_rows)
        for kind, record in records:
            target_id, _ = self._reference(kind, record)
            candidates[target_id] = (kind, record)
        self._candidates = candidates
        self._catalog = catalog

    def _reference(self, kind, record):
        identity = describe(kind, record)
        key = kind + ':' + encoded(identity['locator'])
        row = self._registered.get(key)
        if row and kind == 'artist' and not same_artist(json.loads(row['identity_snapshot_json']), record[1]):
            key += ':' + hashlib.sha256(encoded(identity).encode()).hexdigest()
            row = self._registered.get(key)
        if row is not None:
            return row['id'], key
        # Artist identity is part of an unregistered draft reference, protecting against ID reuse.
        reference = key
        if kind == 'artist':
            reference += ':' + hashlib.sha256(encoded(identity).encode()).hexdigest()
        return str(uuid5(NAMESPACE_URL, 'anisongdb:contribution:' + reference)), key

    def _preview(self, kind, record, connection):
        target_id, _ = self._reference(kind, record)
        values = field_values(kind, record[1] if kind == 'artist' else [record])
        return {
            'id': target_id,
            'kind': kind,
            **describe(kind, record),
            'values': values,
            'versions': {
                field: connection.version(target_id, field, self.loaded_revision) for field in values
            },
        }

    def _register_target(self, target_id, catalog, connection):
        self._index_targets(catalog, connection)
        candidate = self._candidates.get(target_id)
        if candidate is None:
            raise ContributionConflict('The catalog record changed. Select the record again.')
        kind, record = candidate
        reference_id, key = self._reference(kind, record)
        identity = describe(kind, record)
        target = {
            'id': reference_id, 'lookup_key': key, 'kind': kind,
            'locator_json': encoded(identity['locator']),
            'identity_snapshot_json': encoded(identity),
        }
        values = self.target_values(catalog, target)
        connection.insert_target(
            reference_id,
            key,
            kind,
            target['locator_json'],
            target['identity_snapshot_json'],
            now(),
        )
        for field, value in values.items():
            self.base_values.setdefault((reference_id, field), value)
        return target

    def search_targets(self, catalog, kind, search, limit):
        term = search.strip().casefold()
        if not term:
            return []
        if kind == "artist":
            records = [
                (artist_id, artist)
                for artist_id, artist in catalog.artists_by_id.items()
                if term
                in " ".join(
                    (*artist.names, *artist.original_names, artist.disambiguation or "")
                ).casefold()
                or term == str(artist_id)
            ]
        elif kind == "anime":
            records = [
                entry.songs[0]
                for ann_id, entry in catalog.anime_by_id.items()
                if any(term in name.value.casefold() for name in entry.search_names)
                or term == str(ann_id)
            ]
        else:
            records = [
                song
                for song in catalog.song_rows
                if term
                in " ".join(
                    filter(
                        None,
                        [
                            song.romaji_song_name,
                            song.original_song_name,
                            song.romaji_song_artist,
                            song.anime_jp_name,
                            song.anime_en_name,
                        ],
                    )
                ).casefold()
                or term in {str(song.ann_song_id), str(song.amq_song_id)}
            ]
        with self.store.connection() as connection:
            self._index_targets(catalog, connection)
            return [self._preview(kind, record, connection) for record in records[:limit]]

    def target_values(self, catalog, target):
        try:
            resolved = resolve(
                target, catalog.songs_by_ann_id, catalog.songs_by_ann_song_id, catalog.artists_by_id
            )
            return field_values(target["kind"], resolved)
        except ValueError as error:
            raise ContributionConflict(str(error)) from error

    def display_target(self, catalog, target):
        """Build current presentation without rewriting the saved identity snapshot."""
        identity = json.loads(target["identity_snapshot_json"])
        if target["kind"] == "artist":
            artist_id = json.loads(target["locator_json"])["artist_id"]
            identity["detail"] = artist_detail(artist_id, identity.get("disambiguation"))
        elif target["kind"] == "song":
            try:
                song = resolve(
                    target,
                    catalog.songs_by_ann_id,
                    catalog.songs_by_ann_song_id,
                    catalog.artists_by_id,
                )[0]
                identity = describe("song", song)
            except ValueError:
                anime_label = identity.get("anime_label", identity["detail"].rsplit(" · ", 1)[0])
                identity["detail"] = anime_label
                if "song_type" in identity:
                    identity["detail"] += " · " + song_type_label(
                        identity["song_type"], identity["song_number"]
                    )
        return identity

    def submit(self, data, catalog):
        digest = hashlib.sha256(
            data.model_dump_json(exclude={"client_request_id"}).encode()
        ).hexdigest()
        with self.store.connection(write=True) as connection:
            previous = connection.submission_by_request(str(data.client_request_id))
            if previous:
                if previous["payload_hash"] != digest:
                    raise ContributionConflict("This submission identifier was already used for different changes."
                    )
                return previous["id"]
            verified = []
            for item in data.changes:
                target = connection.target(str(item.target_id))
                if target is None:
                    target = self._register_target(str(item.target_id), catalog, connection)
                if item.field not in FIELDS[target["kind"]]:
                    raise InvalidContribution("Unknown target or contribution field.")
                values = self.target_values(catalog, target)
                if item.base_revision != connection.version(target['id'], item.field, self.loaded_revision):
                    raise ContributionConflict("The active catalog changed. Select the record again.")
                verified.append((item, values[item.field]))
            submission = connection.insert_submission(
                data.contributor_name,
                data.comment,
                now(),
                str(data.client_request_id),
                digest,
            )
            for position, (item, before) in enumerate(verified):
                connection.insert_change(
                    submission,
                    str(item.target_id),
                    item.field,
                    item.operation,
                    encoded(before),
                    encoded(item.payload.model_dump()),
                    item.base_revision,
                    position,
                )
            return submission

    def planned(self, connection, target, field, active):
        value = self.base_values.get((target["id"], field), active)
        rows = list(connection.field_revisions(target['id'], field))
        for row in effective(rows):
            value = operate(value, row["operation"], json.loads(row["approved_value_json"]))
        return value

    def planned_artist_ids(self, connection, catalog):
        """Build the final ID assignments, including approvals waiting for restart."""
        values = {
            (artist_id, field): getattr(artist, FIELDS["artist"][field])
            for artist_id, artist in catalog.artists_by_id.items()
            for field in ARTIST_ID_FIELDS
        }
        targets = {}
        for target in connection.artist_targets():
            try:
                artist = resolve(target, {}, {}, catalog.artists_by_id)
            except ValueError:
                continue
            artist_id = json.loads(target["locator_json"])["artist_id"]
            targets[target["id"]] = artist_id
            for field in ARTIST_ID_FIELDS:
                values[(artist_id, field)] = self.base_values.get(
                    (target["id"], field), getattr(artist, FIELDS["artist"][field])
                )
        rows = list(connection.revisions_for_fields(tuple(ARTIST_ID_FIELDS)))
        for row in effective(rows):
            artist_id = targets.get(row["target_id"])
            if artist_id is not None:
                key = (artist_id, row["field"])
                values[key] = operate(
                    values[key], row["operation"], json.loads(row["approved_value_json"])
                )
        return values

    def validate_artist_id_assignments(self, connection, catalog, fields):
        owners = {}
        for (artist_id, field), value in self.planned_artist_ids(connection, catalog).items():
            if field not in fields or value is None:
                continue
            previous = owners.setdefault((field, value), artist_id)
            if previous != artist_id:

                def label(identifier):
                    return f"#{identifier} ({' / '.join(catalog.artists_by_id[identifier].names)})"

                raise ContributionConflict(f"{FIELD_DEFINITIONS[field].label} {value} is assigned to both artists "
                    f"{label(previous)} and {label(artist_id)}. Correct or clear the conflicting assignment.",
                )

    @staticmethod
    def event_data(row):
        return {
            "id": row["id"],
            "reviewer_name": row["reviewer_name"],
            "action": row["action"],
            "reviewed_value": (
                json.loads(row["reviewed_value_json"]) if row["reviewed_value_json"] else None
            ),
            "comment": row["comment"],
            "created_at": row["created_at"],
        }

    def target(self, catalog, target_id):
        with self.store.connection() as connection:
            target = connection.target(target_id)
            if target is None:
                self._index_targets(catalog, connection)
                candidate = self._candidates.get(target_id)
                if candidate is None:
                    raise ContributionNotFound('Record does not exist or has changed. Select it again.')
                return self._preview(*candidate, connection)
            values = self.target_values(catalog, target)
            return {
                'id': target['id'], 'kind': target['kind'],
                **self.display_target(catalog, target), 'values': values,
                'versions': {
                    field: connection.version(target_id, field, self.loaded_revision) for field in values
                },
            }

    def queue(self, catalog, status, before, limit, kind=None, search=""):
        with self.store.connection() as connection:
            rows = connection.submissions(status, before, limit, kind, search)
            has_more = len(rows) > limit
            rows = rows[:limit]
            submissions = [
                {
                    "id": row["id"],
                    "contributor_name": row["contributor_name"],
                    "comment": row["comment"],
                    "submitted_at": row["submitted_at"],
                    "change_count": row["change_count"],
                }
                for row in rows
            ]
            counts = dict(connection.status_counts())
            latest = connection.latest_revision()
            waiting = connection.waiting_fields(self.loaded_revision)
            issue_count = connection.issue_count(self.load_id)
            return {
                "submissions": submissions,
                "next_before": rows[-1]["id"] if has_more else None,
                "counts": counts,
                "loaded_revision": self.loaded_revision,
                "latest_revision": latest,
                "waiting_for_restart": waiting,
                "issue_count": issue_count,
            }

    def submission(self, catalog, submission_id):
        with self.store.connection() as connection:
            submission = connection.submission(submission_id)
            if submission is None:
                raise ContributionNotFound("Submission does not exist.")
            changes = list(connection.submission_changes(submission_id))
            target_ids = tuple(dict.fromkeys(row["target_id"] for row in changes))
            targets = {
                row["id"]: row
                for row in connection.targets_by_ids(target_ids)
            }
            revisions = list(connection.revisions_for_targets(target_ids))
            by_field = defaultdict(list)
            by_change = {}
            for revision in revisions:
                by_field[(revision["target_id"], revision["field"])].append(revision)
                by_change[revision["change_id"]] = revision["revision"]
            id_owners = defaultdict(list)
            if any(row["field"] in ARTIST_ID_FIELDS for row in changes):
                for (artist_id, field), value in self.planned_artist_ids(
                    connection, catalog
                ).items():
                    if value is not None:
                        id_owners[(field, value)].append(artist_id)
            active_targets = {}
            for target_id, target in targets.items():
                try:
                    active_targets[target_id] = (self.target_values(catalog, target), None)
                except ContributionError as error:
                    active_targets[target_id] = ({}, str(error))
            planned_fields = {}
            items = []
            for change in changes:
                target = targets[change["target_id"]]
                active_values, conflict = active_targets[target["id"]]
                field = change["field"]
                active = active_values.get(field)
                key = (target["id"], field)
                field_rows = by_field[key]
                if key not in planned_fields:
                    value = self.base_values.get(key, active)
                    for revision in effective(field_rows):
                        value = operate(
                            value,
                            revision["operation"],
                            json.loads(revision["approved_value_json"]),
                        )
                    planned_fields[key] = value
                proposed = json.loads(change["proposed_value_json"])
                warnings = []
                if (
                    not conflict
                    and field in ARTIST_ID_FIELDS
                    and change["operation"] == "set"
                    and change["review_status"] != "approved"
                ):
                    artist_id = json.loads(target["locator_json"])["artist_id"]
                    for owner in id_owners.get((field, proposed["value"]), ()):
                        if owner != artist_id:
                            warnings.append(
                                f"{FIELD_DEFINITIONS[field].label} {proposed['value']} is already approved for artist #{owner}. Amend the ID or resolve the other assignment before approving."
                            )
                items.append(
                    {
                        "id": change["id"],
                        "target_id": change["target_id"],
                        "field": field,
                        "operation": change["operation"],
                        "proposed_value": proposed,
                        "reviewed_value": (
                            json.loads(change["last_reviewed_value_json"])
                            if change["last_reviewed_value_json"]
                            else proposed
                        ),
                        "review_status": change["review_status"],
                        "review_version": change["review_version"],
                        "target": self.display_target(catalog, target),
                        "active_value": active,
                        "planned_value": planned_fields[key],
                        "field_revision": field_rows[-1]["revision"] if field_rows else 0,
                        "latest_approved_revision": by_change.get(change["id"], 0),
                        "conflict": conflict,
                        "warnings": warnings,
                        "event_count": change["event_count"],
                    }
                )
            return {
                "id": submission["id"],
                "contributor_name": submission["contributor_name"],
                "comment": submission["comment"],
                "submitted_at": submission["submitted_at"],
                "change_count": len(items),
                "changes": items,
            }

    def history(self, change_id, offset, limit):
        with self.store.connection() as connection:
            if not connection.change(change_id):
                raise ContributionNotFound("Change does not exist.")
            total = connection.history_count(change_id)
            rows = connection.review_events(change_id, limit, offset)
            return {"events": [self.event_data(row) for row in rows], "total": total}

    def issues(self, offset, limit):
        with self.store.connection() as connection:
            total = connection.issue_count(self.load_id)
            rows = connection.load_issues(self.load_id, limit, offset)
            return {
                "issues": [
                    {
                        "approved_revision": row["approved_revision"],
                        "target": json.loads(row["identity_snapshot_json"]),
                        "reason": row["reason"],
                    }
                    for row in rows
                ],
                "total": total,
            }

    def decide(self, decisions, name, catalog):
        with self.store.connection(write=True) as connection:
            initial_versions = {}
            changed_id_fields = set()
            for decision in decisions:
                change = connection.change(decision.change_id)
                if not change:
                    raise ContributionNotFound("Change does not exist.")
                if change["review_version"] != decision.expected_review_version:
                    raise ContributionConflict("Another reviewer changed this item. Refresh the queue."
                    )
                if change["review_status"] == "approved":
                    raise ContributionConflict("This item was already approved. Use undo instead.")
                target = connection.target(change['target_id'])
                payload = decision.payload or ContributionPayload.model_validate_json(
                    change["proposed_value_json"]
                )
                if decision.action == "approve":
                    if change["field"] in ARTIST_ID_FIELDS:
                        changed_id_fields.add(change["field"])
                    active = self.target_values(catalog, target)[change["field"]]
                    key = (target["id"], change["field"])
                    initial_versions.setdefault(key, connection.version(*key))
                    if decision.expected_field_revision != initial_versions[key]:
                        raise ContributionConflict("Another approval changed this field. Refresh the queue."
                        )
                    try:
                        validate_operation(change["field"], change["operation"], payload)
                    except ValueError as error:
                        raise InvalidContribution(str(error)) from error
                    planned = self.planned(connection, target, change["field"], active)
                    if change["field"] in ALIASES:
                        removed = (
                            payload.old_value
                            if change["operation"] == "replace_alias"
                            else payload.value
                        )
                        if change["operation"] in {"replace_alias", "remove_alias"} and not any(
                            same_name(value, removed) for value in planned or []
                        ):
                            raise ContributionConflict("The alias is no longer present in the approved values. Refresh and review this change again.",
                            )
                        if change["operation"] == "add_alias" and any(
                            same_name(value, payload.value) for value in planned or []
                        ):
                            raise ContributionConflict("This alias is already approved. Mark the proposal as a duplicate.",
                            )
                event = connection.insert_review_event(
                    change['id'],
                    name,
                    decision.action,
                    encoded(payload.model_dump()),
                    decision.comment,
                    now(),
                )
                if decision.action == "approve":
                    parent = connection.version(target['id'], change['field'])
                    connection.insert_revision(
                        change['id'],
                        event,
                        target['id'],
                        change['field'],
                        change['operation'],
                        encoded(payload.model_dump()),
                        parent,
                        now(),
                    )
                status = {
                    "approve": "approved",
                    "reject": "rejected",
                    "hold": "held",
                    "duplicate": "duplicate",
                }[decision.action]
                connection.update_change(status, change['id'])
            if changed_id_fields:
                # Validate the whole batch so an explicit ID transfer is order-independent.
                self.validate_artist_id_assignments(connection, catalog, changed_id_fields)

    def revert(self, data, name, catalog):
        with self.store.connection(write=True) as connection:
            target_id = str(data.target_id)
            if connection.version(target_id, data.field) != data.expected_revision:
                raise ContributionConflict("The field changed. Refresh before undoing.")
            row = connection.revision(data.expected_revision, target_id, data.field)
            if row is None:
                raise ContributionNotFound("Revision does not exist.")
            event = connection.insert_undo_event(row['change_id'], name, 'revert', data.comment, now())
            connection.insert_revert(
                row['change_id'],
                event,
                target_id,
                data.field,
                'revert',
                '{}',
                row['revision'],
                row['revision'],
                now(),
            )
            connection.update_change(
                'approved' if row['operation'] == 'revert' else 'reverted',
                row['change_id'],
            )
            if data.field in ARTIST_ID_FIELDS:
                self.validate_artist_id_assignments(connection, catalog, {data.field})
