"""Pure contribution operations and revision cancellation rules."""

import unicodedata


def same_name(left, right):
    return unicodedata.normalize("NFC", left) == unicodedata.normalize("NFC", right)


def operate(current, operation, payload):
    if operation == "set":
        return payload["value"]
    if operation == "clear":
        return None
    values = list(current or [])
    removed = payload.get("old_value") if operation == "replace_alias" else payload.get("value")
    if operation in {"replace_alias", "remove_alias"}:
        values = [value for value in values if not same_name(value, removed)]
    if operation in {"add_alias", "replace_alias"} and not any(
        same_name(value, payload["value"]) for value in values
    ):
        values.append(payload["value"])
    return values


def effective(rows):
    """A reversion cancels a revision; undoing that reversion restores it."""
    cancelled = set()
    for row in reversed(rows):
        if row["revision"] not in cancelled and row["reverts_revision"] is not None:
            cancelled.add(row["reverts_revision"])
    return [
        row for row in rows if row["revision"] not in cancelled and row["reverts_revision"] is None
    ]
