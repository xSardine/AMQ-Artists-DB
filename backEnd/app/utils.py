import re
from datetime import datetime, time as dt_time, timezone
from re import Pattern
from typing import Any
from zoneinfo import ZoneInfo

from db_types import *
from schemas import RankedTimeStatus

# Fuzzy-match rules for romaji and visually similar Unicode characters.
# The scanner matches multi-character inputs before single characters so each part
# of the original query is expanded once without reprocessing generated regex.
# Uppercase and lowercase Unicode variants are explicitly included where fuzzy
# equivalence requires both forms.
REGEX_REPLACE_RULES = [
    {"input": "ļ", "replace": "[ļĻ]"},
    {"input": "ł", "replace": "[łŁ]"},
    {"input": "l", "replace": "[l˥ļĻΛłŁ]"},
    {"input": "ψ", "replace": "[ψΨ]"},
    {"input": "ź", "replace": "[źŹ]"},
    {"input": "ż", "replace": "[żŻ]"},
    {"input": "z", "replace": "[zźŹżŻ]"},
    {"input": "ū", "replace": "[ūŪ]"},
    {"input": "ú", "replace": "[úÚ]"},
    {"input": "ü", "replace": "[üÜ]"},
    {"input": "ou", "replace": "(ou|ō|o)"},
    {"input": "uu", "replace": "(uu|u|ū)"},
    {"input": "u", "replace": "([uūŪûúÚùüÜǖμυ]|uu)"},
    {"input": "ω", "replace": "[ωΩ]"},
    {"input": "ō", "replace": "[ōŌ]"},
    {"input": "φ", "replace": "[φΦ]"},
    {"input": "ø", "replace": "[øØ]"},
    {"input": "ó", "replace": "[óÓ]"},
    {"input": "ö", "replace": "[öÖ]"},
    {"input": "0", "replace": "[0Ө]"},
    {"input": "oo", "replace": "(oo|ō|o)"},
    {"input": "oh", "replace": "(oh|ō|o)"},
    {"input": "wo", "replace": "(wo|o)"},
    {"input": "o", "replace": "([oōŌóÓòöÖôøØ0ӨφΦο]|ou|oo|oh|wo)"},
    {"input": "w", "replace": "[wω]"},
    {"input": "aa", "replace": "(aa|a)"},
    {"input": "ae", "replace": "(ae|æ)"},
    {"input": "λ", "replace": "[λΛ]"},
    {"input": "ⓐ", "replace": "[ⓐⒶ]"},
    {"input": "à", "replace": "[àÀ]"},
    {"input": "á", "replace": "[áÁ]"},
    {"input": "ά", "replace": "[άΆ]"},
    {"input": "ā", "replace": "[āĀ]"},
    {"input": "å", "replace": "[åÅ]"},
    {"input": "a", "replace": "([aəäãάΆ@âàÀáÁạåÅæāĀ∀λΛ]|aa)"},
    {"input": "ↄ", "replace": "[ↄↃ]"},
    {"input": "c", "replace": "[cςč℃⊃ↄↃϛ]"},
    {"input": "é", "replace": "[éÉ]"},
    {"input": "ë", "replace": "[ëË]"},
    {"input": "ǝ", "replace": "[ǝƎ]"},
    {"input": "e", "replace": "[eəéÉêёëËèæēǝƎ]"},
    {"input": "'", "replace": "['’ˈ]"},
    {"input": "n", "replace": "[nñň]"},
    {"input": "2", "replace": "[2²₂]"},
    {"input": "3", "replace": "[3³]"},
    {"input": "5", "replace": "[5⁵]"},
    {"input": "*", "replace": "[*✻＊✳︎]"},
    {"input": "ii", "replace": "(ii|i)"},
    {"input": "i", "replace": "([iíίɪ]|ii)"},
    {"input": "x", "replace": "[x×]"},
    {"input": "b", "replace": "[bßβ]"},
    {"input": "ss", "replace": "(ss|ß)"},
    {"input": "я", "replace": "[яЯ]"},
    {"input": "r", "replace": "[rяЯ]"},
    {"input": "s", "replace": "[sς]"},
    {"input": "y", "replace": "[y¥γ]"},
    {"input": "p", "replace": "[pρ]"},
]

# Lookup tables built once at import; _apply_regex_rules scans left-to-right only
REGEX_REPLACEMENTS = {
    rule["input"]: rule["replace"]
    for rule in REGEX_REPLACE_RULES
    if rule["input"] != " "
}

# Mapping of single-character input rules to their regex replacements
SINGLE_CHAR_REPLACEMENTS = {
    rule_input: replacement
    for rule_input, replacement in REGEX_REPLACEMENTS.items()
    if len(rule_input) == 1
}

# Multi-character rules grouped by first character and ordered longest-first
MULTI_CHAR_RULES_BY_FIRST_CHAR: dict[str, tuple[str, ...]] = {}

for rule_input in REGEX_REPLACEMENTS:
    if len(rule_input) <= 1:
        continue

    first_char = rule_input[0]
    existing_rules = MULTI_CHAR_RULES_BY_FIRST_CHAR.get(first_char, ())
    MULTI_CHAR_RULES_BY_FIRST_CHAR[first_char] = tuple(
        sorted(
            (*existing_rules, rule_input),
            key=len,
            reverse=True,
        )
    )


def _apply_regex_rules(search: str) -> str:
    """Expand escaped search text into a fuzzy regex body.

    Uses longest-match rule selection and processes only the original input,
    preventing generated regex fragments from being expanded again.
    Literal spaces become flexible separator patterns.
    """
    result = []
    index = 0

    while index < len(search):
        char = search[index]

        # Replace a typed space with a flexible separator between search terms
        if char == " ":
            result.append(r"[\W_]+")
            index += 1
            continue

        # Prefer the longest multi-character rule at this position
        matched_rule = None
        for rule_input in MULTI_CHAR_RULES_BY_FIRST_CHAR.get(char, ()):
            if search.startswith(rule_input, index):
                matched_rule = rule_input
                break

        if matched_rule is not None:
            result.append(REGEX_REPLACEMENTS[matched_rule])
            index += len(matched_rule)
            continue

        # Otherwise expand this character, or preserve it if no rule exists
        result.append(SINGLE_CHAR_REPLACEMENTS.get(char, char))
        index += 1

    return "".join(result)


def regex_matches(pattern: Pattern[str], text: str, match_case: bool) -> bool:
    """Return whether a compiled pattern matches anywhere in text."""
    if not text:
        return False
    haystack = text if match_case else text.lower()
    return pattern.search(haystack) is not None


def build_search_regex(
    search_text: str,
    partial_match: bool = True,
    match_case: bool = False,
    swap_words: bool = False,
) -> Pattern[str]:
    """Compile user text into a regex with romaji normalization rules applied."""
    # Single-char queries force whole-string regex (^...$) even if partial_match is requested.
    if len(search_text) <= 1:
        partial_match = False

    normalized = search_text if match_case else search_text.lower()
    # Escape regex metacharacters, but leave spaces and * available for custom replacement rules
    escaped = re.escape(normalized).replace("\\ ", " ").replace("\\*", "*")
    pattern = _apply_regex_rules(escaped)
    if not partial_match:
        pattern = f"^{pattern}$"

    # Optionally allow swapped two-word queries (e.g. surname givenname / givenname surname)
    if swap_words:
        words = escaped.split(" ")
        if len(words) == 2:
            swapped = " ".join([words[1], words[0]])
            swapped_pattern = _apply_regex_rules(swapped)
            if not partial_match:
                swapped_pattern = f"^{swapped_pattern}$"
            pattern = f"({pattern})|({swapped_pattern})"

    return re.compile(pattern)


def has_search_text(search_filter) -> bool:
    """True when a text search filter is present with non-whitespace query text."""
    return search_filter is not None and bool(search_filter.search.strip())


def _names_for_artist(artist_database: ArtistDatabase, artist_id: int) -> list[str]:
    """Return an artist's names, falling back to the artist ID when unavailable."""
    artist = artist_database.get(str(artist_id))
    if not artist:
        return [str(artist_id)]
    return artist.get("names") or [str(artist_id)]


def _format_credit_entry(
    artist_database: ArtistDatabase, person_id: int, line_up: int
) -> dict[str, Any]:
    """Build one Artist-shaped credit dict (vocalist, composer, or arranger)."""
    artist = artist_database.get(str(person_id))
    if artist is None:
        return {
            "id": person_id,
            "names": _names_for_artist(artist_database, person_id),
            "line_up_id": line_up,
        }

    entry = {
        "id": person_id,
        "names": artist.get("names") or [str(person_id)],
        "line_up_id": line_up,
    }

    # Expand group line-up members when line_up_id is a real index (not -1).
    line_ups = artist.get("line_ups") or []
    if line_up >= 0 and line_up < len(line_ups):
        entry["members"] = [
            {"id": member[0], "names": _names_for_artist(artist_database, member[0])}
            for member in line_ups[line_up]["members"]
        ]

    groups = artist.get("groups") or []
    if groups:
        entry["groups"] = []
        added_group = set()
        for group in groups:
            # Same group can appear on multiple line-ups; only emit once per group id.
            group_id = int(group[0])
            if group_id in added_group:
                continue
            added_group.add(group_id)
            entry["groups"].append(
                {"id": group_id, "names": _names_for_artist(artist_database, group_id)}
            )

    return entry


def format_song(artist_database: ArtistDatabase, song: SongFullRow) -> FormattedSong:
    """Turn a raw songsFull DB tuple into the API SongEntry-shaped dict.

    Credit columns store comma-separated artist IDs and parallel line-up indexes.
    line_up indexes into artist_database[id]['line_ups']; -1 means no line-up slot.
    """
    if song[COL_SONG_TYPE] == 1:
        song_type = "Opening " + str(song[17])
    elif song[COL_SONG_TYPE] == 2:
        song_type = "Ending " + str(song[17])
    else:
        song_type = "Insert Song"

    artists = []
    if song[COL_ARTISTS]:
        artists.extend(
            _format_credit_entry(artist_database, int(artist_id), int(line_up))
            for artist_id, line_up in zip(song[COL_ARTISTS].split(","), song[COL_ARTISTS_LINE_UP].split(","))
        )

    composers = []
    if song[COL_COMPOSERS]:
        composers.extend(
            _format_credit_entry(artist_database, int(composer_id), int(line_up))
            for composer_id, line_up in zip(song[COL_COMPOSERS].split(","), song[COL_COMPOSERS_LINE_UP].split(","))
        )

    arrangers = []
    if song[COL_ARRANGERS]:
        arrangers.extend(
            _format_credit_entry(artist_database, int(arranger_id), int(line_up))
            for arranger_id, line_up in zip(song[COL_ARRANGERS].split(","), song[COL_ARRANGERS_LINE_UP].split(","))
        )


    songinfo: FormattedSong = {
        "annId": song[0],
        "linked_ids": {
            "myanimelist": song[1],
            "anidb": song[2],
            "anilist": song[3],
            "kitsu": song[4],
        },
        "animeJPName": song[6] or song[7],
        "animeENName": song[7] or song[6],
        "animeAltName": song[9].split("\\$") if song[9] else [],  # alt names stored delimited by $
        "animeVintage": song[10],
        "animeType": song[11],
        "animeCategory": song[12],
        "annSongId": song[14],
        "amqSongId": song[15],
        "songType": song_type,
        "songCategory": song[18],
        "songName": song[20],
        "songArtist": song[22] or "",
        "songComposer": song[26] or "",
        "songArranger": song[30] or "",
        "songDifficulty": song[33],
        "isDub": song[34],
        "isRebroadcast": song[35],
        "songLength": song[36],
        "HQ": song[37],
        "MQ": song[38],
        "audio": song[39],
        "artists": artists,
        "composers": composers,
        "arrangers": arrangers,
    }

    return songinfo


# AMQ ranked runs from 20:30 to 21:23 local time in each region.
RANKED_REGIONS = [
    ("Europe/Copenhagen", "Central"),
    ("America/Chicago", "Western"),
    ("Asia/Tokyo", "Eastern"),
]
RANKED_START_TIME = dt_time(hour=20, minute=30)
RANKED_END_TIME = dt_time(hour=21, minute=23)
RANKED_REGION_ZONES = [ZoneInfo(tz) for (tz, _) in RANKED_REGIONS]
RANKED_REGION_LABELS = [label for (_, label) in RANKED_REGIONS]


def is_ranked_time() -> bool:
    """True when AMQ ranked is active in any tracked region."""
    now_utc = datetime.now(timezone.utc)
    for tz_info in RANKED_REGION_ZONES:
        local_t = now_utc.astimezone(tz_info).time()
        if RANKED_START_TIME <= local_t < RANKED_END_TIME:
            return True
    return False


def get_ranked_time_info(date: datetime | None = None) -> RankedTimeStatus:
    """Ranked status, active region, time remaining, and server time."""
    if date is None:
        dt_utc = datetime.now(timezone.utc)
    else:
        dt_utc = (
            date.astimezone(timezone.utc)
            if date.tzinfo
            else date.replace(tzinfo=timezone.utc)
        )
    server_time = dt_utc.isoformat()

    for index, tz_info in enumerate(RANKED_REGION_ZONES):
        local_dt = dt_utc.astimezone(tz_info)
        local_t = local_dt.time()
        if RANKED_START_TIME <= local_t < RANKED_END_TIME:
            local_end = local_dt.replace(
                hour=RANKED_END_TIME.hour,
                minute=RANKED_END_TIME.minute,
                second=0,
                microsecond=0,
            )
            remaining_total_seconds = max(0, int((local_end - local_dt).total_seconds()))
            return RankedTimeStatus(
                active=True,
                region=RANKED_REGION_LABELS[index],
                remaining_minutes=remaining_total_seconds // 60,
                remaining_seconds=remaining_total_seconds % 60,
                server_time=server_time,
            )

    return RankedTimeStatus(
        active=False,
        region=None,
        remaining_minutes=None,
        remaining_seconds=None,
        server_time=server_time,
    )
