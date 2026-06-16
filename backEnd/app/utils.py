import re
from datetime import datetime, time as dt_time, timezone
from zoneinfo import ZoneInfo

from schemas import RankedTimeStatus

ANIME_REGEX_REPLACE_RULES = [
    # Ļ can't lower correctly with sqlite lower function
    {"input": "ļ", "replace": "[ļĻ]"},
    # Ł can't lower correctly with sqlite lower function
    {"input": "ł", "replace": "[łŁ]"},
    {"input": "l", "replace": "[l˥ļĻΛłŁ]"},
    # Ψ can't lower correctly with sqlite lower function
    {"input": "ψ", "replace": "[ψΨ]"},
    # Ź can't lower correctly with sqlite lower function
    {"input": "ź", "replace": "[źŹ]"},
    # Ż can't lower correctly with sqlite lower function
    {"input": "ż", "replace": "[żŻ]"},
    {"input": "z", "replace": "[zźŹżŻ]"},
    # Ū can't lower correctly with sqlite lower function
    {"input": "ū", "replace": "[ūŪ]"},
    # Ú can't lower correctly with sqlite lower function
    {"input": "ú", "replace": "[úÚ]"},
    # Ü can't lower correctly with sqlite lower function
    {"input": "ü", "replace": "[üÜ]"},
    {"input": "ou", "replace": "(ou|ō|o)"},
    {"input": "uu", "replace": "(uu|u|ū)"},
    {"input": "u", "replace": "([uūŪûúÚùüÜǖμυ]|uu)"},
    # Ω can't lower correctly with sqlite lower function
    {"input": "ω", "replace": "[ωΩ]"},
    # Ō can't lower correctly with sqlite lower function
    {"input": "ō", "replace": "[ōŌ]"},
    # Φ can't lower correctly with sqlite lower function
    {"input": "φ", "replace": "[φΦ]"},
    # Ø can't lower correctly with sqlite lower function
    {"input": "ø", "replace": "[øØ]"},
    # Ó can't lower correctly with sqlite lower function
    {"input": "ó", "replace": "[óÓ]"},
    # Ö can't lower correctly with sqlite lower function
    {"input": "ö", "replace": "[öÖ]"},
    {"input": "0", "replace": "[0Ө]"},
    {"input": "oo", "replace": "(oo|ō|o)"},
    {"input": "oh", "replace": "(oh|ō|o)"},
    {"input": "wo", "replace": "(wo|o)"},
    {"input": "o", "replace": "([oōŌóÓòöÖôøØ0ӨφΦο]|ou|oo|oh|wo)"},
    {"input": "w", "replace": "[wω]"},
    {"input": "aa", "replace": "(aa|a)"},
    {"input": "ae", "replace": "(ae|æ)"},
    # Λ can't lower correctly with sqlite lower function
    {"input": "λ", "replace": "[λΛ]"},
    # Ⓐ can't lower correctly with sqlite lower function
    {"input": "ⓐ", "replace": "[ⓐⒶ]"},
    # À can't lower correctly with sqlite lower function
    {"input": "à", "replace": "[àÀ]"},
    # Á can't lower correctly with sqlite lower function
    {"input": "á", "replace": "[áÁ]"},
    # ά can't lower correctly with sqlite lower function
    {"input": "ά", "replace": "[άΆ]"},
    # Ā can't lower correctly with sqlite lower function
    {"input": "ā", "replace": "[āĀ]"},
    # Å can't lower correctly with sqlite lower function
    {"input": "å", "replace": "[åÅ]"},
    {"input": "a", "replace": "([aəäãάΆ@âàÀáÁạåÅæāĀ∀λΛ]|aa)"},
    # ↄ can't lower correctly with sqlite lower function
    {"input": "ↄ", "replace": "[ↄↃ]"},
    {"input": "c", "replace": "[cςč℃⊃ↄↃϛ]"},
    # É can't lower correctly with sqlite lower function
    {"input": "é", "replace": "[éÉ]"},
    # Ë can't lower correctly with sqlite lower function
    {"input": "ë", "replace": "[ëË]"},
    # Ǝ can't lower correctly with sqlite lower function
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
    # я can't lower correctly with sqlite lower function
    {"input": "я", "replace": "[яЯ]"},
    {"input": "r", "replace": "[rяЯ]"},
    {"input": "s", "replace": "[sς]"},
    {"input": "y", "replace": "[y¥γ]"},
    {"input": "p", "replace": "[pρ]"},
    {
        "input": " ",
        "replace": "([^\\w]+|_+)",
    },
]


def escape_regexp(text: str) -> str:
    """Escape user input for regex, but keep literal spaces and asterisks searchable."""
    return re.escape(text).replace("\\ ", " ").replace("\\*", "*")


def apply_regex_rules(search):
    """Expand normalized query text using ANIME_REGEX_REPLACE_RULES."""
    for rule in ANIME_REGEX_REPLACE_RULES:
        search = search.replace(rule["input"], rule["replace"])
    return search


def get_regex_search(og_search, partial_match=True, swap_words=False, match_case=False):
    """Build a regex pattern from user text with romaji normalization rules applied."""
    normalized = og_search if match_case else og_search.lower()
    escaped = escape_regexp(normalized)
    pattern = apply_regex_rules(escaped)
    if partial_match:
        pattern = f".*{pattern}.*"
    else:
        pattern = f"^{pattern}$"

    # Optionally, also allow swapped two-word queries (e.g. surname givenname / givenname surname)
    if swap_words:
        words = escaped.split(" ")
        if len(words) == 2:
            swapped = " ".join([words[1], words[0]])
            swapped_pattern = apply_regex_rules(swapped)
            if partial_match:
                swapped_pattern = f".*{swapped_pattern}.*"
            else:
                swapped_pattern = f"^{swapped_pattern}$"
            pattern = f"({pattern})|({swapped_pattern})"

    return pattern


def regex_match(regex, text, match_case=False):
    """Return whether regex matches from the start of text."""
    if not text:
        return False
    try:
        return re.match(regex, text if match_case else text.lower()) is not None
    except re.error:
        return False


def has_search_text(search_filter) -> bool:
    """True when a text search filter is present with non-whitespace query text."""
    return search_filter is not None and bool(search_filter.search.strip())


def _names_for_artist(artist_database, artist_id) -> list[str]:
    """Romaji names for an artist id, or the id as a single placeholder when the row is missing."""
    artist = artist_database.get(str(artist_id))
    if not artist:
        return [str(artist_id)]
    return artist.get("names") or [str(artist_id)]


def _format_credit_entry(artist_database, person_id, line_up: int) -> dict:
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
            if group[0] in added_group:
                continue
            added_group.add(group[0])
            entry["groups"].append(
                {"id": group[0], "names": _names_for_artist(artist_database, group[0])}
            )

    return entry


def format_song(artist_database, song):
    """Turn a raw songsFull DB tuple into the API SongEntry-shaped dict.

    Credit columns store comma-separated artist IDs and parallel line-up indexes.
    line_up indexes into artist_database[id]['line_ups']; -1 means no line-up slot.
    """
    if song[16] == 1:
        type = "Opening " + str(song[17])
    elif song[16] == 2:
        type = "Ending " + str(song[17])
    else:
        type = "Insert Song"

    artists = []
    if song[23]:
        for artist_id, line_up in zip(song[23].split(","), song[24].split(",")):
            artists.append(_format_credit_entry(artist_database, artist_id, int(line_up)))

    # Composer and arranger blocks mirror the artist credit shape (IDs at 27/31, line-ups at 28/32).
    composers = []
    if song[27]:
        for composer_id, line_up in zip(song[27].split(","), song[28].split(",")):
            composers.append(_format_credit_entry(artist_database, composer_id, int(line_up)))

    arrangers = []
    if song[31]:
        for arranger_id, line_up in zip(song[31].split(","), song[32].split(",")):
            arrangers.append(_format_credit_entry(artist_database, arranger_id, int(line_up)))

    songinfo = {
        "annId": song[0],
        "linked_ids": {
            "myanimelist": song[1],
            "anidb": song[2],
            "anilist": song[3],
            "kitsu": song[4],
        },
        "animeJPName": song[6] or song[7],
        "animeENName": song[7] or song[6],
        "animeAltName": song[9].split("\\$") if song[9] else song[9],  # alt names stored delimited by $
        "animeVintage": song[10],
        "animeType": song[11],
        "animeCategory": song[12],
        "annSongId": song[14],
        "amqSongId": song[15],
        "songType": type,
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


# AMQ ranked window: 20:30–21:23 local in Central, Western, or Eastern regions.
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
