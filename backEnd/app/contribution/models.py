from dataclasses import dataclass
from typing import Annotated, Literal, get_args
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

Kind = Literal["anime", "artist", "song"]
ContributionField = Literal[
    "anime_original_title",
    "anime_original_alias",
    "artist_original_alias",
    "song_original_title",
    "song_original_performer_credit",
    "song_original_composer_credit",
    "song_original_arranger_credit",
    "artist_ann_id",
    "artist_mal_id",
    "artist_anilist_id",
]
Operation = Literal["set", "clear", "add_alias", "replace_alias", "remove_alias"]
ANN_ARTIST_URL = "https://www.animenewsnetwork.com/encyclopedia/people.php?id="
MAL_ARTIST_URL = "https://myanimelist.net/people/"
ANILIST_ARTIST_URL = "https://anilist.co/staff/"
MAX_ARTIST_ID = 9007199254740991  # Exact integer range supported by browser JSON.
SQLITE_MAX_INTEGER = 9_223_372_036_854_775_807


@dataclass(frozen=True)
class FieldDefinition:
    kind: Kind
    attribute: str
    value_type: Literal["text", "aliases", "integer"]
    label: str
    profile_prefix: str | None = None


FIELD_DEFINITIONS = {
    "anime_original_title": FieldDefinition(
        "anime", "original_jp_name", "text", "Original anime title"
    ),
    "anime_original_alias": FieldDefinition(
        "anime", "original_alt_names", "aliases", "Original anime alias"
    ),
    "artist_original_alias": FieldDefinition(
        "artist", "original_names", "aliases", "Original artist alias"
    ),
    "artist_ann_id": FieldDefinition(
        "artist", "ann_id", "integer", "ANN artist ID", ANN_ARTIST_URL
    ),
    "artist_mal_id": FieldDefinition(
        "artist", "mal_id", "integer", "MyAnimeList artist ID", MAL_ARTIST_URL
    ),
    "artist_anilist_id": FieldDefinition(
        "artist", "anilist_id", "integer", "AniList artist ID", ANILIST_ARTIST_URL
    ),
    "song_original_title": FieldDefinition(
        "song", "original_song_name", "text", "Original song title"
    ),
    "song_original_performer_credit": FieldDefinition(
        "song", "original_song_artist", "text", "Original performer credit"
    ),
    "song_original_composer_credit": FieldDefinition(
        "song", "original_song_composer", "text", "Original composer credit"
    ),
    "song_original_arranger_credit": FieldDefinition(
        "song", "original_song_arranger", "text", "Original arranger credit"
    ),
}
FIELDS = {
    kind: {key: field.attribute for key, field in FIELD_DEFINITIONS.items() if field.kind == kind}
    for kind in get_args(Kind)
}
ALIASES = {key for key, field in FIELD_DEFINITIONS.items() if field.value_type == "aliases"}
ARTIST_ID_FIELDS = {
    key for key, field in FIELD_DEFINITIONS.items() if field.value_type == "integer"
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContributionPayload(StrictModel):
    value: Annotated[str, Field(strict=True, max_length=500)] | StrictInt | None = None
    old_value: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def clean(self):
        for name in ("value", "old_value"):
            value = getattr(self, name)
            if isinstance(value, str):
                value = value.strip()
                if not value or any(ord(character) < 32 for character in value):
                    raise ValueError("Names must be nonempty single-line text.")
                setattr(self, name, value)
        return self


def validate_operation(field: str, operation: str, payload: ContributionPayload) -> None:
    allowed = (
        {"add_alias", "replace_alias", "remove_alias"} if field in ALIASES else {"set", "clear"}
    )
    if operation not in allowed:
        raise ValueError("Operation does not match this contribution field.")
    if operation != "clear" and payload.value is None:
        raise ValueError("A value is required.")
    if operation == "clear" and (payload.value is not None or payload.old_value is not None):
        raise ValueError("Clear must not include a value.")
    if operation == "replace_alias" and payload.old_value is None:
        raise ValueError("The alias being replaced is required.")
    if operation != "replace_alias" and payload.old_value is not None:
        raise ValueError("Only alias replacement accepts an old value.")
    if operation != "clear":
        if field in ARTIST_ID_FIELDS:
            if type(payload.value) is not int or not 1 <= payload.value <= MAX_ARTIST_ID:
                raise ValueError("Artist IDs must be positive integers within the supported range.")
        elif not isinstance(payload.value, str):
            raise ValueError("Names must be text.")


class ChangeInput(StrictModel):
    target_id: UUID
    field: ContributionField
    operation: Operation
    payload: ContributionPayload
    base_revision: int = Field(ge=0, le=SQLITE_MAX_INTEGER)

    @model_validator(mode="after")
    def validate_change(self):
        validate_operation(self.field, self.operation, self.payload)
        return self


class SubmissionInput(StrictModel):
    contributor_name: str = Field(min_length=1, max_length=100)
    comment: str = Field(default="", max_length=3000)
    client_request_id: UUID
    changes: list[ChangeInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_submission(self):
        self.contributor_name = self.contributor_name.strip()
        if not self.contributor_name or any(
            ord(character) < 32 for character in self.contributor_name
        ):
            raise ValueError("Contributor name is required.")
        keys = [
            (str(c.target_id), c.field, c.operation, c.payload.model_dump_json())
            for c in self.changes
        ]
        if len(keys) != len(set(keys)):
            raise ValueError("The submission contains an identical change twice.")
        return self


class Decision(StrictModel):
    change_id: int = Field(gt=0, le=SQLITE_MAX_INTEGER)
    action: Literal["approve", "reject", "hold", "duplicate"]
    expected_review_version: int = Field(ge=0, le=SQLITE_MAX_INTEGER)
    expected_field_revision: int = Field(ge=0, le=SQLITE_MAX_INTEGER)
    payload: ContributionPayload | None = None
    comment: str = Field(default="", max_length=3000)


class Decisions(StrictModel):
    decisions: list[Decision] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_changes(self):
        if len({d.change_id for d in self.decisions}) != len(self.decisions):
            raise ValueError("Each change can be decided only once per request.")
        return self


class Revert(StrictModel):
    target_id: UUID
    field: ContributionField
    expected_revision: int = Field(gt=0, le=SQLITE_MAX_INTEGER)
    comment: str = Field(default="", max_length=3000)
