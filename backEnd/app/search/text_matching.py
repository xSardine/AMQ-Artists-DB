"""Fuzzy text matching rules for search names."""

import re
from re import Pattern

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
