"""Prepare compressed JSON and ETags at startup, then serve cached responses."""

import gzip
import hashlib
import json
from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import Response
from pydantic import TypeAdapter

from api.presenters import format_annid_linked_ids, format_catalog_dump
from api.schemas import AnnIdLinkedAnimeEntry
from catalog.models import Catalog


@dataclass(frozen=True)
class CachedJson:
    """A precompressed JSON body and its validator for the original JSON bytes."""

    body: bytes
    etag: str

    @classmethod
    def from_payload(cls, payload: object) -> "CachedJson":
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        etag = f'W/"{hashlib.sha256(encoded).hexdigest()}"'
        return cls(gzip.compress(encoded, compresslevel=9), etag)


@dataclass(frozen=True)
class CachedResponses:
    annid_linked_ids: CachedJson
    catalog_dump: CachedJson


def build_cached_responses(catalog: Catalog) -> CachedResponses:
    linked_ids_adapter = TypeAdapter(dict[int, AnnIdLinkedAnimeEntry])
    linked_ids = linked_ids_adapter.dump_python(
        linked_ids_adapter.validate_python(format_annid_linked_ids(catalog)),
        mode="json",
        by_alias=False,
    )
    return CachedResponses(
        annid_linked_ids=CachedJson.from_payload(linked_ids),
        catalog_dump=CachedJson.from_payload(format_catalog_dump(catalog)),
    )


def gzip_json_response(request: Request, cached: CachedJson) -> Response:
    """Serve cached JSON with its existing compression and conditional-response policy."""
    headers = {
        "Cache-Control": "public, max-age=3600",
        "ETag": cached.etag,
        "Content-Encoding": "gzip",
    }
    if request.headers.get("if-none-match") == cached.etag:
        return Response(status_code=304, headers=headers)
    return Response(content=cached.body, media_type="application/json", headers=headers)
