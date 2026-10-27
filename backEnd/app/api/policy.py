"""Shared classification for credential handling, cache policy, and log exclusion."""

PRIVATE_API_PREFIXES = (
    "/api/log/",
    "/api/review/",
    "/api/contribution-targets",
    "/api/contributions",
)


def is_private_api(path: str) -> bool:
    return any(
        path == prefix.rstrip("/")
        or path.startswith(prefix if prefix.endswith("/") else prefix + "/")
        for prefix in PRIVATE_API_PREFIXES
    )
