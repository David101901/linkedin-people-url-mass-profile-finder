import logging
from typing import Any, Dict, List, Optional, Tuple

# Simulated in-memory profile "database".
# In a real-world system this would be replaced with compliant data sources or APIs.
_SAMPLE_PROFILES: List[Dict[str, Any]] = [
    {
        "name": "John Malkovich",
        "company": "Malkovich Enterprises",
        "linkedinUrl": "https://www.linkedin.com/in/john-malkovich-374ab741",
        "position": "CEO - Malkovich",
        "language": "English",
    },
    {
        "name": "Jane Doe",
        "company": "Acme Corp",
        "linkedinUrl": "https://www.linkedin.com/in/jane-doe-acme",
        "position": "Head of Growth",
        "language": "English",
    },
    {
        "name": "Carlos García",
        "company": "DataVision",
        "linkedinUrl": "https://www.linkedin.com/in/carlos-garcia-datavis",
        "position": "Data Scientist",
        "language": "Spanish",
    },
]

def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().lower()

def _match_profile(
    name: str,
    company: Optional[str],
    language: Optional[str],
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Try to match a profile from the in-memory sample dataset.

    Returns a tuple of (matching_profiles, status_hint).
    Status hint is one of: "success", "ambiguous", "not_found".
    """
    n_name = _normalize(name)
    n_company = _normalize(company)
    n_language = _normalize(language)

    matches: List[Dict[str, Any]] = []

    for profile in _SAMPLE_PROFILES:
        p_name = _normalize(profile.get("name"))
        p_company = _normalize(profile.get("company"))
        p_lang = _normalize(profile.get("language"))

        if p_name != n_name:
            continue

        if n_company and p_company != n_company:
            # If company is provided, require it to match.
            continue

        if n_language and p_lang != n_language:
            # If language preference is provided, require match.
            continue

        matches.append(profile)

    if not matches:
        # Try a softer match on just the name if we were strict before.
        for profile in _SAMPLE_PROFILES:
            p_name = _normalize(profile.get("name"))
            if p_name == n_name:
                matches.append(profile)

    if not matches:
        return [], "not_found"
    if len(matches) == 1:
        return matches, "success"
    return matches, "ambiguous"

def find_profile(
    name: str,
    company: Optional[str],
    language: Optional[str],
    search_query: str,
    logger: Optional[logging.Logger] = None,
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Find a simulated LinkedIn-style profile for the given person.

    This implementation does NOT perform any web scraping or live HTTP requests.
    It only looks up data from a small, static in-memory dataset.
    """
    log = logger or logging.getLogger("profile_finder")

    log.debug(
        "Looking up profile: name=%r, company=%r, language=%r, searchQuery=%r",
        name,
        company,
        language,
        search_query,
    )

    matches, status = _match_profile(name=name, company=company, language=language)

    if status == "not_found":
        log.info("No profile found for %r", name)
        return None, "not_found"

    if status == "ambiguous":
        # Choose the first one deterministically but mark as ambiguous.
        chosen = matches[0]
        log.warning(
            "Multiple profiles found for %r, returning the first match: %r",
            name,
            chosen.get("linkedinUrl"),
        )
        return chosen, "ambiguous"

    # Success with a single match
    chosen = matches[0]
    log.info(
        "Profile match for %r -> %s",
        name,
        chosen.get("linkedinUrl"),
    )
    return chosen, "success"