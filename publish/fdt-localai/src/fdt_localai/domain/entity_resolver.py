"""Two-layer Entity Resolver as specified in ARCHITECTURE.md §4.2 (Finding F16)."""

from __future__ import annotations

import difflib
import re
from fdt_localai.domain.models import StructuralLocation


def _normalize_token(s: str) -> str:
    """Normalize structural location string for lexical matching."""
    s_clean = re.sub(r"\.(nrang|rang)\.(out|in)$", "", s.strip(), flags=re.IGNORECASE)
    s_clean = re.sub(r"\.ctl$", "", s_clean, flags=re.IGNORECASE)
    return re.sub(r"[^a-z0-9]+", "_", s_clean.lower()).strip("_")


class EntityResolver:
    """Resolves location names and aliases across FEM, Spectrum, and Calc Sheets."""

    def __init__(self, locations: list[StructuralLocation] | None = None) -> None:
        self._locations: dict[str, StructuralLocation] = {}
        self._alias_map: dict[str, str] = {}
        if locations:
            for loc in locations:
                self.register(loc)

    def register(self, loc: StructuralLocation) -> None:
        """Register a canonical location and its aliases."""
        self._locations[loc.canonical_id] = loc
        self._alias_map[_normalize_token(loc.canonical_id)] = loc.canonical_id
        for alias in loc.aliases:
            self._alias_map[_normalize_token(alias)] = loc.canonical_id

    def resolve(self, raw_name: str, fuzzy_threshold: float = 0.85) -> str | None:
        """Resolve a raw location identifier to its canonical_id."""
        norm = _normalize_token(raw_name)
        if norm in self._alias_map:
            return self._alias_map[norm]

        # Layer 2: Fuzzy lexical match
        candidates = list(self._alias_map.keys())
        if not candidates:
            return None

        try:
            from rapidfuzz import fuzz, process  # type: ignore

            match = process.extractOne(norm, candidates, scorer=fuzz.WRatio)
            if match and (match[1] / 100.0) >= fuzzy_threshold:
                return self._alias_map[match[0]]
        except ImportError:
            matches = difflib.get_close_matches(
                norm, candidates, n=1, cutoff=fuzzy_threshold
            )
            if matches:
                return self._alias_map[matches[0]]
        return None
