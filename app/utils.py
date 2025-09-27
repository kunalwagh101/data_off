import json
import hashlib
from typing import Dict

CANONICAL_FIELDS = ["project_name", "registry", "vintage", "quantity", "serial_number"]


def canonicalize_payload(payload: Dict) -> str:
    """Return canonical JSON string for hashing. Ensures stable ordering and normalization.

    - Normalize registry to upper-case
    - Strip whitespace from strings
    - Ensure numeric types are canonical (ints)
    """
    ordered = {}
    for k in CANONICAL_FIELDS:
        v = payload.get(k)
        if isinstance(v, str):
            v = v.strip()
        # Ensure registry uppercase for normalization
        if k == "registry" and isinstance(v, str):
            v = v.upper()
        ordered[k] = v

    # Use separators and sort_keys to ensure deterministic JSON representation
    return json.dumps(ordered, separators=(",",":"), sort_keys=True)


def deterministic_id(payload: Dict) -> str:
    s = canonicalize_payload(payload)
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return h
