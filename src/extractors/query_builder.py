from typing import Optional

def build_search_query(
    name: str,
    company: Optional[str] = None,
    position: Optional[str] = None,
    language: Optional[str] = None,
) -> str:
    """
    Build a human-readable search query description for a person.

    This does not perform any HTTP calls; it just returns a string that
    describes how one *might* look up a professional profile for the person.
    """
    parts = [name]

    if company:
        parts.append(f'"{company}"')

    if position:
        parts.append(position)

    if language:
        parts.append(f"language:{language}")

    # Intentionally generic and non-engine-specific query description.
    return "professional profile search: " + " ".join(parts)